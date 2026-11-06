"""
Generate `docs/api/` from the OpenAPI of the running code.

    python -m tools.api_docs          # (re)write docs/api/
    make docs-api                     # same, from the repo root

The docs are derived, never hand-edited: the endpoint list, parameters,
bodies, responses and schemas come from `app.openapi()` (public API) and
`core_openapi_schema()` (control plane). The only thing added on top is each
route's **guard**, read from its dependency chain — the OpenAPI does not say
which permission or Core scope protects a route.

`tests/test_contracts/test_api_docs.py` fails when `docs/api/` drifts from the
code; regenerate with this command (or `UPDATE_CONTRACT_SNAPSHOTS=1`).
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi.routing import APIRoute

from app.main import app
from app.modules.provisioning.router.tenants import core_openapi_schema

DOCS_DIR = Path(__file__).resolve().parents[1] / "docs" / "api"
HEADER = (
    "<!-- Gerado por backend/tools/api_docs.py a partir do OpenAPI. "
    "Não edite à mão: rode `make docs-api`. -->"
)
METHOD_ORDER = {"get": 0, "post": 1, "put": 2, "patch": 3, "delete": 4}


@dataclass(frozen=True)
class Group:
    file: str
    title: str
    intro: str


# OpenAPI tag → document. A new tag without an entry here fails the test, so a
# new module is never left undocumented by accident.
PUBLIC_GROUPS: dict[str, Group] = {
    "auth": Group(
        "auth.md",
        "Autenticação",
        "Login da equipe, renovação rotativa do token, logout e o perfil da sessão. "
        "A barbearia vem do domínio de acesso (em dev, do header `X-Tenant-Slug`).",
    ),
    "shop": Group(
        "shop.md",
        "Barbearia",
        "Dados e configuração da barbearia da sessão e as unidades visíveis ao usuário.",
    ),
    "team": Group(
        "team.md",
        "Equipe e convites",
        "Membros, convites e o aceite de convite — inclusive o primeiro acesso do dono de "
        "uma barbearia recém-provisionada.",
    ),
    "barbers": Group(
        "barbers.md",
        "Barbeiros",
        "Cadastro dos profissionais que atendem (coluna da agenda, comissão). Separado do "
        "cadastro de usuários com acesso ao painel: um não cria o outro, e o vínculo é opcional.",
    ),
    "catalog": Group(
        "catalog.md",
        "Catálogo",
        "Serviços da barbearia (um preço para todas as unidades, em centavos) e os serviços "
        "que cada barbeiro faz.",
    ),
    "clients": Group(
        "clients.md",
        "Clientes",
        "Clientes da barbearia, compartilhados entre as unidades e identificados pelo "
        "telefone em E.164.",
    ),
    "infra": Group("infra.md", "Infraestrutura", "Sondas de saúde."),
}
CORE_GROUP = Group(
    "control-plane.md",
    "Control plane (`/core/*`)",
    "Criação e ciclo de vida das barbearias, chamado pelo Core da plataforma. Autenticação "
    "própria pelo header `X-Core-Key`; fora do `/docs` público — o contrato também é servido "
    "em `GET /core/openapi.json`, atrás da chave.",
)


# --------------------------------------------------------------------------- #
# Guards (not in the OpenAPI)
# --------------------------------------------------------------------------- #


def _api_routes(routes) -> list[APIRoute]:
    found: list[APIRoute] = []
    for route in routes:
        if isinstance(route, APIRoute):
            found.append(route)
        elif (inner := getattr(route, "original_router", None)) is not None:
            found.extend(_api_routes(inner.routes))
    return found


def _guards(dependant) -> list[str]:
    found: list[str] = []
    for dep in dependant.dependencies:
        call = dep.call
        for cell in getattr(call, "__closure__", None) or ():
            value = cell.cell_contents
            kind = type(value).__name__
            if kind == "Permission":
                found.append(f"permissão `{value.value}`")
            elif kind == "CoreScope":
                found.append(f"`X-Core-Key` com escopo `{value.value}`")
        if getattr(call, "__name__", "") == "current_user":
            found.append("sessão (`Authorization: Bearer`)")
        found.extend(_guards(dep))
    return found


def guard_table() -> dict[tuple[str, str], str]:
    table: dict[tuple[str, str], str] = {}
    for route in _api_routes(app.routes):
        guards = list(dict.fromkeys(_guards(route.dependant)))
        # A permission implies the session; say only the stronger requirement.
        if any(g.startswith("permissão") for g in guards):
            guards = [g for g in guards if not g.startswith("sessão")]
        for method in route.methods:
            table[(method.lower(), route.path)] = " + ".join(guards) or "pública"
    return table


# --------------------------------------------------------------------------- #
# Schema rendering
# --------------------------------------------------------------------------- #


def prose(text: str) -> str:
    """Free text from docstrings, safe inside Markdown (no stray HTML tags, one line in tables)."""
    return text.strip().replace("<", "&lt;").replace(">", "&gt;")


def anchor(text: str) -> str:
    """GitHub's heading anchor: lowercase, punctuation dropped, spaces → hyphens."""
    text = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
    return re.sub(r"\s", "-", text.strip())


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def type_of(schema: dict[str, Any], refs: set[str]) -> str:
    if "$ref" in schema:
        name = _ref_name(schema["$ref"])
        refs.add(name)
        return f"[`{name}`](#{anchor(name)})"
    if "anyOf" in schema:
        parts = [type_of(s, refs) for s in schema["anyOf"]]
        return " \\| ".join(parts)
    if "enum" in schema:
        return " \\| ".join(f"`{v}`" for v in schema["enum"])
    kind = schema.get("type")
    if kind == "array":
        return f"{type_of(schema.get('items', {}), refs)}[]"
    if kind == "object" and "additionalProperties" in schema:
        return f"objeto de {type_of(schema['additionalProperties'], refs)}"
    if kind == "null":
        return "`null`"
    fmt = schema.get("format")
    return f"`{kind}`" + (f" ({fmt})" if fmt else "") if kind else "`any`"


def _constraints(schema: dict[str, Any]) -> str:
    notes = []
    for key, label in (("minLength", "mín."), ("maxLength", "máx."), ("minimum", "≥")):
        if key in schema:
            notes.append(f"{label} {schema[key]}")
    if "default" in schema and schema["default"] not in (None, [], {}):
        notes.append(f"padrão `{schema['default']}`")
    if schema.get("description"):
        notes.append(prose(schema["description"]).replace("\n", " "))
    return "; ".join(notes)


def render_schema(name: str, schema: dict[str, Any], refs: set[str]) -> list[str]:
    lines = [f"#### {name}", ""]
    if schema.get("description"):
        lines += [prose(schema["description"]), ""]
    if "enum" in schema:
        lines += ["Valores: " + ", ".join(f"`{v}`" for v in schema["enum"]), ""]
        return lines
    props = schema.get("properties", {})
    if not props:
        return lines + [f"Tipo: {type_of(schema, refs)}", ""]
    required = set(schema.get("required", []))
    lines += ["| Campo | Tipo | Obrigatório | Notas |", "|---|---|---|---|"]
    for field, spec in props.items():
        lines.append(
            f"| `{field}` | {type_of(spec, refs)} | {'sim' if field in required else 'não'} "
            f"| {_constraints(spec)} |"
        )
    return lines + [""]


# --------------------------------------------------------------------------- #
# Operations
# --------------------------------------------------------------------------- #


def _body_schema(content: dict[str, Any] | None, refs: set[str]) -> str | None:
    if not content:
        return None
    schema = content.get("application/json", {}).get("schema")
    return type_of(schema, refs) if schema else None


def render_operation(
    method: str, path: str, op: dict[str, Any], guard: str, refs: set[str]
) -> list[str]:
    lines = [f"### {method.upper()} {path}", "", f"**{op.get('summary', '')}**", ""]
    if op.get("description"):
        lines += [prose(op["description"]), ""]
    lines += [f"- **Acesso:** {guard}"]

    params = [p for p in op.get("parameters", []) if p["name"] not in ("authorization",)]
    if params:
        lines += ["- **Parâmetros:**", ""]
        lines += ["  | Nome | Onde | Obrigatório | Tipo |", "  |---|---|---|---|"]
        for p in params:
            note = " (só em dev)" if p["name"] == "x-tenant-slug" else ""
            lines.append(
                f"  | `{p['name']}`{note} | {p['in']} | {'sim' if p.get('required') else 'não'} "
                f"| {type_of(p.get('schema', {}), refs)} |"
            )
        lines.append("")

    body = op.get("requestBody")
    if body:
        lines.append(f"- **Corpo:** {_body_schema(body.get('content'), refs)}")

    lines.append("- **Respostas:**")
    for status, resp in sorted(op.get("responses", {}).items()):
        schema = _body_schema(resp.get("content"), refs)
        desc = resp.get("description", "")
        lines.append(f"  - `{status}` {desc}" + (f" → {schema}" if schema else ""))
    return lines + [""]


def render_group(
    group: Group, operations: list[tuple[str, str, dict]], spec: dict, guards: dict
) -> str:
    refs: set[str] = set()
    body: list[str] = []
    for method, path, op in sorted(operations, key=lambda o: (o[1], METHOD_ORDER[o[0]])):
        body += render_operation(method, path, op, guards.get((method, path), "?"), refs)

    # Every schema referenced, transitively, so each file stands alone.
    components = spec.get("components", {}).get("schemas", {})
    rendered: list[str] = []
    done: set[str] = set()
    while pending := sorted(refs - done):
        for name in pending:
            done.add(name)
            rendered += render_schema(name, components[name], refs)
    schema_blocks = sorted("\n".join(block) for block in _split_blocks(rendered))

    index = [
        f"- [`{m.upper()} {p}`](#{anchor(f'{m} {p}')}) — {op.get('summary', '')}"
        for m, p, op in sorted(operations, key=lambda o: (o[1], METHOD_ORDER[o[0]]))
    ]
    out = [
        HEADER,
        "",
        f"# {group.title}",
        "",
        group.intro,
        "",
        'Erros seguem o formato `{"detail": "<mensagem em português>"}`; validação de entrada '
        "responde `422` com a lista de problemas.",
        "",
        "## Rotas",
        "",
        *index,
        "",
        "## Endpoints",
        "",
        *body,
        "## Schemas",
        "",
        "\n".join(schema_blocks),
    ]
    return "\n".join(out).rstrip() + "\n"


def _split_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    for line in lines:
        if line.startswith("#### "):
            blocks.append([])
        blocks[-1].append(line)
    return blocks


def _operations(spec: dict) -> dict[str, list[tuple[str, str, dict]]]:
    by_tag: dict[str, list[tuple[str, str, dict]]] = {}
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            tag = (op.get("tags") or ["untagged"])[0]
            by_tag.setdefault(tag, []).append((method, path, op))
    return by_tag


def render_all() -> dict[str, str]:
    """File name → content, for every file under docs/api/."""
    guards = guard_table()
    files: dict[str, str] = {}

    public = app.openapi()
    by_tag = _operations(public)
    unknown = set(by_tag) - set(PUBLIC_GROUPS)
    if unknown:
        raise SystemExit(f"tags sem documento em tools/api_docs.py: {sorted(unknown)}")
    for tag, group in PUBLIC_GROUPS.items():
        # frontend/scripts/api-docs.ts links to `<tag>.md`: keep the names aligned.
        assert group.file == f"{tag}.md", f"{tag}: document must be named {tag}.md"
        files[group.file] = render_group(group, by_tag.get(tag, []), public, guards)

    core = core_openapi_schema()
    core_ops = [op for ops in _operations(core).values() for op in ops]
    files[CORE_GROUP.file] = render_group(CORE_GROUP, core_ops, core, guards)

    rows = [
        f"| [{g.title}]({g.file}) | {g.intro.split('.')[0]}. |"
        for g in [*PUBLIC_GROUPS.values(), CORE_GROUP]
    ]
    files["README.md"] = "\n".join(
        [
            HEADER,
            "",
            "# Referência da API",
            "",
            "Gerada do OpenAPI do código (`app.openapi()` e o contrato do control plane). "
            "Para o *porquê* de cada regra, veja as specs em [`../specs/`](../specs/); "
            "para o contrato congelado, `tests/test_contracts/snapshots/`.",
            "",
            "| Documento | Conteúdo |",
            "|---|---|",
            *rows,
            "",
            "## Convenções",
            "",
            "- **Barbearia:** vem do domínio (`<slug>.<BASE_DOMAIN>` ou domínio próprio). Em "
            "desenvolvimento, o header `X-Tenant-Slug` substitui o subdomínio.",
            "- **Sessão:** `Authorization: Bearer <access_token>` (15 min); renovação por "
            "`POST /auth/refresh`. O token só vale no domínio da barbearia que o emitiu.",
            "- **Acesso:** cada rota diz a permissão exigida (mapa em "
            "[`../PERMISSIONS_MAP.md`](../PERMISSIONS_MAP.md)) ou o escopo da `X-Core-Key`.",
            '- **Erros:** `{"detail": "..."}` em português; `422` para validação; `503` quando a '
            "barbearia está em preparação ou manutenção.",
            "",
        ]
    )
    return files


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    files = render_all()
    for name, content in files.items():
        (DOCS_DIR / name).write_text(content, encoding="utf-8")
    stale = {p.name for p in DOCS_DIR.glob("*.md")} - set(files)
    for name in stale:
        (DOCS_DIR / name).unlink()
    print(f"docs/api: {len(files)} arquivos" + (f", removidos {sorted(stale)}" if stale else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
