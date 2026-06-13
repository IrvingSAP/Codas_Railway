/*
 * ***********************************************************************
 * NOMBRE DE ARCHIVO...: SEGFFUSTN3                                      *
 * DESCRIPCION.........: ARCHIVO DE NOVEDADES A ACTUALIZAR EN SEGFFUSNOV *
 * REQUERIMIENTO.......: IEX_DESBLOQUEO USUARIOS ISERIES                 *
 * SUBDOMINIO..........: RIESGOS Y SEGURIDAD                             *
 * FECHA DE CREACIÓN...: 23 DE NOVIEMBRE DE 2019.                        *
 * AUTOR...............: ALEXANDER OLARTE MU#OZ.                         *
 * ***********************************************************************
 *- REGISTRO Y CAMPOS ------------------------------------------
*/

CREATE TABLE &LIB/SEGFFUSTN3 (
  NROID        CHAR(30)   CCSID 284 WITH DEFAULT '',
  FEIAUS       CHAR(10)   CCSID 284 WITH DEFAULT '',
  FEFAUS       CHAR(10)   CCSID 284 WITH DEFAULT '',
  FECRET       CHAR(10)   CCSID 284 WITH DEFAULT '',
  FECHA_ACT    NUMERIC(8) NOT NULL DEFAULT 0,
  HORA_ACT     NUMERIC(6) NOT NULL DEFAULT 0
)
RCDFMT REGUSTN3;

/* DESCRIPCIÓN */
LABEL ON TABLE &LIB/SEGFFUSTN3 IS
'SEG - Archivo noved a actualizar en SEGFFUSNOV';

/* DESCRIPCIÓN CAMPOS */
LABEL ON &LIB/SEGFFUSTN3
(NROID       TEXT IS  'DOCUMENTO IDENTIDAD',
 FEIAUS      TEXT IS  'FECH INICIO AUSENCIA',
 FEFAUS      TEXT IS  'FECHA FIN AUSENCIA',
 FECRET      TEXT IS  'FECHA RETIRO',
 FECHA_ACT   TEXT IS  'FECHA ACTUAL',
 HORA_ACT    TEXT IS  'HORA ACTUAL'
);

/* DESCRIPCIÓN CAMPOS */
LABEL ON &LIB/SEGFFUSTN3
(NROID            IS  'DOCUMENTO_IDENTIDAD',
 FEIAUS           IS  'FECH_INICIO_AUSENCIA',
 FEFAUS           IS  'FECHA_FIN_AUSENCIA',
 FECRET           IS  'FECHA_RETIRO',
 FECHA_ACT        IS  'FECHA_ACTUAL',
 HORA_ACT         IS  'HORA_ACTUAL'
);
