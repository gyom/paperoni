import shutil
import textwrap
from typing import Union

from blessed import Terminal
from ovld import ovld

from .db import schema as sch
from .model import Author, DatePrecision, Paper, Venue, from_dict

T = Terminal()
tw = shutil.get_terminal_size((80, 20)).columns


link_generators = {
    "arxiv": {
        "abstract": "https://arxiv.org/abs/{}",
        "pdf": "https://arxiv.org/pdf/{}.pdf",
    },
    "pubmed": {
        "abstract": "https://pubmed.ncbi.nlm.nih.gov/{}",
    },
    "pmc": {
        "abstract": "https://www.ncbi.nlm.nih.gov/pmc/articles/{}",
    },
    "doi": {
        "abstract": "https://doi.org/{}",
    },
    "openreview": {
        "abstract": "https://openreview.net/forum?id={}",
        "pdf": "https://openreview.net/pdf?id={}",
    },
    "dblp": {"abstract": "https://dblp.uni-trier.de/rec/{}"},
    "semantic_scholar": {
        "abstract": "https://www.semanticscholar.org/paper/{}"
    },
}


def print_field(title, contents, bold=False):
    """Prints a line that goes 'title: contents', nicely formatted."""
    contents = textwrap.fill(f"{title}: {contents}", width=tw)[len(title) + 2 :]
    title = T.bold_cyan(f"{title}:")
    contents = T.bold(contents) if bold else contents
    print(title, contents)


def expand_links(links):
    pref = [
        "arxiv.abstract",
        "arxiv.pdf",
        "pubmed.abstract",
        "openreview.abstract",
        "openreview.pdf",
        "pmc.abstract",
        "dblp.abstract",
        "pdf",
        "doi.abstract",
        "html",
        "semantic_scholar.abstract",
        "corpusid",
        "mag",
        "xml",
        "patent",
        "unknown",
        "unknown_",
    ]
    results = []
    for link in links:
        if link.type in link_generators:
            results.extend(
                (f"{link.type}.{kind}", url.format(link.link))
                for kind, url in link_generators[link.type].items()
            )
        else:
            results.append((link.type, link.link))
    results.sort(key=lambda pair: pref.index(pair[0]) if pair[0] in pref else 1)
    return results


def format_term(self):
    """Print the paper on the terminal."""
    print_field("Title", T.bold(self.title))
    print_field("Authors", ", ".join(auth.name for auth in self.authors))
    for release in self.releases:
        venue = release.venue
        print_field(
            "Date", DatePrecision.format(venue.date, venue.date_precision)
        )
        print_field("Venue", venue.name)
    if self.links:
        print_field("URL", expand_links(self.links)[0][1])


@ovld
def display(d: dict):
    display(from_dict(d))


@ovld
def display(paper: Union[Paper, sch.Paper]):
    """Print the paper in long form on the terminal.

    Long form includes abstract, affiliations, keywords, number of
    citations.
    """
    print_field("Title", paper.title)
    print_field("Authors", "")
    for auth in paper.authors:
        if auth.author:
            print(
                f" * {auth.author.name:30} {', '.join(aff.name for aff in auth.affiliations)}"
            )
        else:
            print(T.bold_red("ERROR: MISSING AUTHOR"))
    print_field("Abstract", paper.abstract)
    print_field("Venue", "")
    for release in paper.releases:
        venue = release.venue
        d = DatePrecision.format(venue.date, venue.date_precision)
        v = venue.name
        print(f"  {T.bold_green(d)} {T.bold_magenta(release.status)} {v}")
    print_field("Topics", ", ".join(t.name for t in paper.topics))
    print_field("Sources", "")
    for typ, link in expand_links(paper.links):
        print(f"  {T.bold_green(typ)} {link}")
    print_field("Citations", paper.citation_count)


@ovld
def display(author: Author):
    """Print an author on the terminal."""
    print_field("Name", T.bold(author.name))
    if author.roles:
        print_field("Affiliations", "")
        for role in author.roles:
            print(
                f"* {role.institution.name:20} as {role.role:20} from {DatePrecision.day.format2(role.start_date)} to {role.end_date and DatePrecision.day.format2(role.end_date) or '-'}"
            )
    print_field("Links", "")
    for typ, link in expand_links(author.links):
        print(f"  {T.bold_green(typ):20} {link}")


@ovld
def display(venue: Venue):
    """Print a release on the terminal."""
    print_field("Venue", T.bold(venue.name))
    print_field("Series", T.bold(venue.series))
    print_field("Type", T.bold(venue.type))
    if venue.aliases:
        print_field("Aliases", "")
        for alias in venue.aliases:
            print(f"* {alias}")
    d = DatePrecision.format(venue.date, venue.date_precision)
    print_field("Date", d)
    print_field("Links", "")
    for typ, link in expand_links(venue.links):
        print(f"  {T.bold_green(typ):20} {link}")