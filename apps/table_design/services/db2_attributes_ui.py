"""Metadatos de UI para atributos DB2 por columna (paso 2 del flujo de campos)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

InputKind = Literal["si", "no"]


@dataclass(frozen=True)
class Db2AttributeUiRow:
    """Fila de la tabla de atributos DB2 (demo / pantalla paso 2)."""

    name: str
    input_kind: InputKind
    example: str
    section: str | None = None
    model_field: str | None = None

    @property
    def field_key(self) -> str:
        return self.model_field or self.name


DB2_ATTRIBUTE_UI_ROWS: tuple[Db2AttributeUiRow, ...] = (
    Db2AttributeUiRow(
        name="ccsid",
        input_kind="si",
        example=(
            "NOMBRE VARCHAR(50) CCSID 1208\n"
            "Útil para UTF-8, EBCDIC, ASCII, etc"
        ),
        section="Declaraciones y validaciones",
    ),
    Db2AttributeUiRow(
        name="is_hidden",
        input_kind="no",
        example="LLAVE_SCRIPT CHAR(32) DEFAULT 'N/A' IMPLICITLY HIDDEN",
        section=None,
    ),
    Db2AttributeUiRow(
        name="default_sql_expression",
        input_kind="si",
        example=(
            "CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
            "IS_ACTIVE SMALLINT DEFAULT 1\n"
            "IS_ACTIVE SMALLINT NOT NULL WITH DEFAULT"
        ),
        section=None,
    ),
    Db2AttributeUiRow(
        name="nullable",
        input_kind="si",
        example="IS_ACTIVE SMALLINT NOT NULL WITH DEFAUL , NOT NULL,",
        section=None,
    ),
    Db2AttributeUiRow(
        name="is_unique",
        input_kind="no",
        example="CODIGO_SKU     VARCHAR(30) UNIQUE,",
        section=None,
    ),
    Db2AttributeUiRow(
        name="check_constraint_sql",
        input_kind="si",
        example="STATUS CHAR(1) CHECK (STATUS IN ('A','I','P'))",
        section=None,
    ),
    Db2AttributeUiRow(
        name="generated_expression",
        input_kind="si",
        example=(
            "NOMBRE_COMPLETO VARCHAR(120) GENERATED ALWAYS AS "
            "(TABLE_NAME_SHORT CONCAT '-' CONCAT TABLE_NAME_LONG)"
        ),
        section=None,
    ),
    Db2AttributeUiRow(
        name="fieldproc_program",
        input_kind="si",
        example="DOCUMENTO VARCHAR(20) FIELDPROC CODASLIB/ENCRIPTAR_DOC",
        section="Protección y compresión",
    ),
    Db2AttributeUiRow(
        name="for_bit_data",
        input_kind="no",
        example="TOKEN VARBINARY(64) FOR BIT DATA",
        section=None,
    ),
    Db2AttributeUiRow(
        name="compress_mode",
        input_kind="si",
        example="DESCRIPCION VARCHAR(200) COMPRESS SYSTEM DEFAULT",
        section=None,
    ),
    Db2AttributeUiRow(
        name="is_masked",
        input_kind="si",
        example="EMAIL VARCHAR(254) MASKED WITH (FUNCTION 'EMAIL')",
        model_field="mask_function",
        section=None,
    ),
    Db2AttributeUiRow(
        name="user_defined_field",
        input_kind="si",
        example=(
            "Definido por el usuario, definiciones personales o atributos "
            "que no estan presentes en esta seleccion"
        ),
        section="Definido por el Usuario",
    ),
)

DB2_UI_FIELD_KEYS: frozenset[str] = frozenset(r.field_key for r in DB2_ATTRIBUTE_UI_ROWS)
