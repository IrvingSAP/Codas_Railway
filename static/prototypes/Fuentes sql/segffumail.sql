/*
 * ***********************************************************************
 * NOMBRE DE CROGRAMA..: SEGFFUMAIL                                      *
 * DESCRIPCIÓN.........: ARCHIVO DE CORREOS DE USUARIOS ISERIES          *
 * REQUERIMIENTO.......: PMO25818 - IEX_DESBLOQUEO USUARIOS ISERIES      *
 * SUBDOMINIO..........: RIESGOS Y SEGURIDAD                             *
 * FECHA DE CREACIÓN...: 27 DE JUNIO DE 2018.                            *
 * AUTOR...............: ALEXANDER OLARTE MU#OZ.                         *
 * ***********************************************************************
 *- REGISTRO Y CAMPOS ------------------------------------------
*/
CREATE TABLE   &LIB/SEGFFUMAIL(
   NUM_IDENTI  CHAR (15)   NOT NULL DEFAULT '' ,
   CORREO_USU  CHAR (150)  NOT NULL DEFAULT ''
)
RCDFMT REGUMAIL;

/* DESCRIPCIÓN */
LABEL ON TABLE &LIB/SEGFFUMAIL IS
'Archivo de Correos de Usuarios iSeries';

/* DESCRIPCIÓN CAMPOS */
LABEL ON &LIB/SEGFFUMAIL
(NUM_IDENTI  TEXT IS  'NUMERO DE IDENTIFIC',
 CORREO_USU  TEXT IS  'CORREO DE USUARIO'
);

/* DESCRIPCIÓN CAMPOS */
LABEL ON COLUMN &LIB/SEGFFUMAIL
(NUM_IDENTI       IS  'NUM_IDENTIFIC',
 CORREO_USU       IS  'CORREO_USUARIO'
);
