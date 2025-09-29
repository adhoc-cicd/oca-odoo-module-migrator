# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
# This script is based on the original code from:
# https://github.com/odoo/odoo/blob/master/odoo/upgrade_code/17.5-00-tree-to-list.py

from odoo_module_migrate.base_migration_script import BaseMigrationScript

import ast
import json
import re


def upgrade_sql_constraints(
    logger, module_path, module_name, manifest_path, migration_steps, tools
):
    # Odoo method in which we migrate all occurrences of _sql_constraints
    files_to_process = tools.get_files(module_path, (".py",))
    sql_expression_re = re.compile(r"\b_sql_constraints\s*=\s*\[([^\]]+)]")
    ind = " " * 4

    # Function to build the new SQL constraint definition
    def build_sql_object(match):
        constraints = ast.literal_eval("[" + match.group(1) + "]")
        result = []
        for name, definition, *messages in constraints:
            message = messages[0] if messages else ""
            constructor = "Constraint"
            if message:
                # format on 2 lines
                message_repr = json.dumps(
                    message, ensure_ascii=False
                )  # so that the message is in double quotes
                args = f"\n{ind * 2}{definition!r},\n{ind * 2}{message_repr},\n{ind}"
            elif len(definition) > 60:
                args = f"\n{ind * 2}{definition!r}"
            else:
                args = repr(definition)
            result.append(f"_{name} = models.{constructor}({args})")
        return f"\n{ind}".join(result)

    # Process each file
    for file in files_to_process:
        content = tools._read_content(file)
        content = sql_expression_re.sub(build_sql_object, content)
        if sql_expression_re.search(content):
            logger.warning("Failed to replace sql_constraints")
        tools._write_content(file, content)


class MigrationScript(BaseMigrationScript):

    _GLOBAL_FUNCTIONS = [upgrade_sql_constraints]
    
    # (extensions, regexes, prompt)
    _AI_TRANSFORMS = [
        (
            [".py"],
            [
                r"expression\.AND\s*\(",
                r"expression\.OR\s*\(",
                r"Domain\.(AND|OR)\s*\(\s*\[",
            ],
            """# Prompt: Refactorización de Domains

    Analiza el siguiente código de Odoo y determina si corresponde aplicar una refactorización de **domains**:

    - Sustituir `expression.AND([...])` → `Domain.AND([...])` o el uso de `&`.
    - Sustituir `expression.OR([...])` → `Domain.OR([...])` o el uso de `|`.
    - Simplificar dominios anidados usando `&` y `|`.

    ### Reglas
    - Si se detecta este patrón, devolver un objeto JSON con `show_change: true` y en `content` incluir únicamente el **código refactorizado**.
    - Si no corresponde, devolver `show_change: false` y `content: ""`.""",
        ),
        (
            [".py"],
            [
                r"_notify_progress\s*\(",
                r"_trigger\s*\(",
                r"\[:\s*batch_size\s*\]",
            ],
            """# Prompt: Migración de Métodos en Crons

Analiza el siguiente código de Odoo y determina si corresponde aplicar la migración de métodos en **crons**:

- Sustituir llamadas a `_notify_progress` por `_commit_progress`.
- Ejecutar un primer `_commit_progress(remaining=<total_len>)` antes de iniciar las iteraciones, indicando el total de registros a procesar **(sin try/except)**.
- Dentro del bucle, llamar a `_commit_progress(processed=1)` después de cada registro procesado **(cada llamada debe ir dentro de un bloque `try/except`)**.
- En caso de excepción dentro del bucle, ejecutar `self.env.cr.rollback()`.
- Si antes se usaban batches (`[:batch_size]`) y `_trigger`, eliminar tanto el slicing de batches como el uso de `_trigger`.

### Reglas
- El refactor **solo aplica si el código contiene `_notify_progress` o `_trigger` usado dentro de un cron iterativo por lotes**.
- **No refactorizar** métodos que solo contienen un `_trigger` suelto sin bucle ni batches.
- Si corresponde aplicar el refactor, devolver un objeto JSON con `show_change: true` y en `content` incluir únicamente el **código refactorizado**.
- Si no corresponde, devolver `show_change: false` y `content: ""`.

---

### Ejemplo genérico válido

#### Antes

```python
batch_size = 100
data = <code>
total_len = len(data)
batch_size = min(total_len, batch_size)
for i, rec in enumerate(data[:batch_size]):
    <code>
    self.env["ir.cron"]._notify_progress(done=i + 1, remaining=batch_size - (i + 1))

if total_len > batch_size:
    self.env.ref("saas_provider_upgrade.ir_cron_update_client_data_records")._trigger()
```

#### Después

```python
data = <code>
total_len = len(data)
self.env["ir.cron"]._commit_progress(remaining=total_len)
for rec in data:
    try:
        <code>
        self.env["ir.cron"]._commit_progress(processed=1)
    except Exception:
        self.env.cr.rollback()
```""",
        ),
    ]
