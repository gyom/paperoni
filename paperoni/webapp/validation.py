from pathlib import Path

from aiostream import stream
from hrepr import H
from starbear import Queue, Reference
from starbear.constructors import BrowserEvent

from .common import SearchGUI, config, mila_template
from .render import validation_html
from .utils import db_logger

here = Path(__file__).parent


@mila_template(help="/help#validation")
async def app(page, box):
    """Validate papers."""
    q = Queue()
    action_q = Queue().wrap(refs=True)
    area = H.div["area"].autoid()

    with config().database as db:
        gui = SearchGUI(
            page,
            db,
            q,
            dict(page.query_params),
            defaults={"validation": "not-processed", "limit": 100},
        )
        box.print(gui)
        box.print(
            H.div["helpbox"](
                H.span["ball"]("?"),
                " Please view ",
                H.a(
                    "the help section", href="/help#validation", target="_blank"
                ),
                " for instructions as to how to use this functionality.",
            )
        )
        box.print(area)

        # This list holds the papers that are in the interface so that they are not
        # garbage-collected.
        paper_hold = []

        def reset():
            box[area].clear()
            paper_hold.clear()

        async for result in stream.merge(action_q, gui.loop(reset=reset)):
            if isinstance(result, BrowserEvent):
                paper = result.obj
                match result.tag:
                    case "valid":
                        db.remove_flags(paper, "validation")
                        db.insert_flag(paper, "validation", 1)
                    case "invalid":
                        db.remove_flags(paper, "validation")
                        db.insert_flag(paper, "validation", 0)
                    case "unknown":
                        db.remove_flags(paper, "validation")

                # Communicate feedback to the browser. Indexing a page with result.ref
                # selects the element that has the matching --ref attribute.
                page[result.ref].do(
                    f"this.setAttribute('status', '{result.tag}')"
                )

                user = page.session.get("user", {}).get("email", None)
                db_logger.info(
                    f"User set validation='{result.tag}' on paper {paper.title} "
                    f"({paper.paper_id.hex()})",
                    extra={"user": user},
                )

            else:
                paper_hold.append(result)
                div = validation_html(result)
                existing_flag = db.get_flag(result, "validation")

                match existing_flag:
                    case 0:
                        existing_status = "invalid"
                    case 1:
                        existing_status = "valid"
                    case _:
                        existing_status = "unknown"

                val_div = H.div["validation-buttons"](
                    div,
                    H.div(
                        H.button["valid"](
                            "Yes",
                            # Events put into action_q.tag("valid") will have
                            # event.tag == "valid", this is how we know which button
                            # was pressed.
                            onclick=action_q.tag("valid"),
                        ),
                        H.button["invalid"](
                            "No",
                            onclick=action_q.tag("invalid"),
                        ),
                        H.button["unknown"](
                            "Unknown",
                            onclick=action_q.tag("unknown"),
                        ),
                    ),
                    # This property is used for styling, see the stylesheet
                    status=existing_status,
                    # This embeds an identifier in the --ref attribute of this div.
                    # Any event fired from inside the div will have the hierarchy of
                    # these references in event.refs, and the closest object in
                    # event.obj. This means we can recover the result object from
                    # the button presses.
                    __ref=Reference(result),
                )

                box[area].print(val_div)


ROUTES = app
