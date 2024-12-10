import docutils.nodes as nodes
import yaml
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

_endpoint_format = """\
.. dropdown:: :bdg-primary:`{verb}` {name}
   :color: {color}

   {summary}
   {description}
"""


class IncludeOpenAPI(SphinxDirective):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {"filter-tags": directives.unchanged}

    def run(self):
        source = directives.uri(self.arguments[0])
        with open(source, "r") as f:
            data = yaml.safe_load(f)
        return [
            node
            for name, path in data["paths"].items()
            for node in self.render_path(name, path)
        ]

    def render_path(self, name: str, path: dict) -> list[nodes.Node]:
        return [
            node
            for verb, ep in path.items()
            if verb
            in (
                "delete",
                "connect",
                "get",
                "head",
                "options",
                "patch",
                "post",
                "put",
                "trace",
            )
            for node in self.render_endpoint(name, verb, ep)
        ]

    def render_endpoint(self, name: str, verb: str, endpoint: dict) -> list[nodes.Node]:
        include = (
            len(
                set(endpoint.get("tags", [])).intersection(
                    self.options["filter-tags"].split(",")
                )
            )
            > 0
        )
        if not include:
            return []
        color = {
            "get": "dark",
            "patch": "warning",
            "delete": "danger",
            "put": "secondary",
        }.get(verb, "muted")
        para: nodes.Element = nodes.paragraph(translatable=False)
        self.state.nested_parse(
            StringList(
                _endpoint_format.format(
                    name=name,
                    verb=verb.upper(),
                    color=color,
                    description=endpoint.get("description", ""),
                    summary=endpoint.get("summary", ""),
                ).splitlines()
            ),
            0,
            para,
        )
        return [para]


def setup(sphinx: Sphinx):
    sphinx.add_directive("include-openapi", IncludeOpenAPI)
