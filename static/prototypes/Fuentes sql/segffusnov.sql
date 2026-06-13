/*
 * ***********************************************************************
 * NOMBRE DE ARCHIVO...: SEGFFUSNOV                                      *
 * DESCRIPCION.........: ARCHIVO DE NOVEDADES USUARIOS ISERIES           *
 * REQUERIMIENTO.......: PMO25818 - IEX_DESBLOQUEO USUARIOS ISERIES      *
 * SUBDOMINIO..........: RIESGOS Y SEGURIDAD                             *
 * FECHA DE CREACIÓN...: 19 DE JUNIO DE 2018.                            *
 * AUTOR...............: ALEXANDER OLARTE MU#OZ.                         *
 * ***********************************************************************
 *- REGISTRO Y CAMPOS ------------------------------------------
*/

CREATE TABLE &LIB/SEGFFUSNOV (
  NROID        CHAR(30)   CCSID 284 WITH DEFAULT '',
  FEIAUS       CHAR(10)   CCSID 284 WITH DEFAULT '',
  FEFAUS       CHAR(10)   CCSID 284 WITH DEFAULT '',
  FECRET       CHAR(10)   CCSID 284 WITH DEFAULT '',
  FECHA_ACT    NUMERIC(8) NOT NULL DEFAULT 0,
  HORA_ACT     NUMERIC(6) NOT NULL DEFAULT 0
)
RCDFMT REGUSNOV;

/* DESCRIPCIÓN */
LABEL ON TABLE &LIB/SEGFFUSNOV IS
'Archivo de Novedades Usuarios iSeries';

/* DESCRIPCIÓN CAMPOS */
LABEL ON &LIB/SEGFFUSNOV
(NROID       TEXT IS  'DOCUMENTO IDENTIDAD',
 FEIAUS      TEXT IS  'FECH INICIO AUSENCIA',
 FEFAUS      TEXT IS  'FECHA FIN AUSENCIA',
 FECRET      TEXT IS  'FECHA RETIRO',
 FECHA_ACT   TEXT IS  'FECHA ACTUAL',
 HORA_ACT    TEXT IS  'HORA ACTUAL'
);

/* DESCRIPCIÓN CAMPOS */
LABEL ON &LIB/SEGFFUSNOV
(NROID            IS  'DOCUMENTO_IDENTIDAD',
 FEIAUS           IS  'FECH_INICIO_AUSENCIA',
 FEFAUS           IS  'FECHA_FIN_AUSENCIA',
 FECRET           IS  'FECHA_RETIRO',
 FECHA_ACT        IS  'FECHA_ACTUAL',
 HORA_ACT         IS  'HORA_ACTUAL'
);
