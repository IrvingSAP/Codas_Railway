--***********************************************************************
--***********************************************************************
--NOMBRE DE CROGRAMA..: SEGTBLOUSR                                      *
--DESCRIPCIÓN.........: ARCHIVO HISTORICO DE DETALLE DE NOVEDADES DE    *
--                      CREACION DE USARIOS ISERIES                     *
--REQUERIMIENTO.......: PMO25818 - CREACION DE  USUARIOS ISERIES USM    *
--SUBDOMINIO..........: RIESGOS Y SEGURIDAD                             *
--FECHA DE CREACIÓN...: 28  DE ENERO DE 2022.                           *
--AUTOR...............: CARLOS ROJAS                                    *
--***********************************************************************
-- REGISTRO Y CAMPOS ------------------------------------------
--
CREATE TABLE   &LIB/SEGTBLOUSR(
   USUARIO     CHAR (10)   NOT NULL DEFAULT '' ,
   FECHMODIF   NUMERIC(8)  NOT NULL DEFAULT 0  ,
   HORAMODIF   NUMERIC(6)  NOT NULL DEFAULT 0  ,
   ESTADO      NUMERIC(1)  NOT NULL DEFAULT 0  ,
   CORREO_USU  CHAR (150)  NOT NULL DEFAULT '' ,
   DETALL_ACC  CHAR (500)  NOT NULL DEFAULT ''
)
RCDFMT REGDBDUSU;

-- /* DESCRIPCIÓN */
LABEL ON TABLE &LIB/SEGTBLOUSR IS
'Archivo Detalle Log Desbloqueo Automático Usuarios';

-- /* DESCRIPCIÓN CAMPOS */
LABEL ON &LIB/SEGTBLOUSR
(USUARIO     TEXT IS  'PERFIL DE USUARIO',
 FECHMODIF   TEXT IS  'FECHA MODIFICACION',
 HORAMODIF   TEXT IS  'HORA MODIFICACION',
 ESTADO      TEXT IS  'ESTADO/FASE ACTUAL',
 CORREO_USU  TEXT IS  'CORREO DE USUARIO',
 DETALL_ACC  TEXT IS  'DETALLE DE LA ACCION'
);
-- /* DESCRIPCIÓN CAMPOS */
LABEL ON COLUMN &LIB/SEGTBLOUSR
(USUARIO          IS  'PERFIL_USUARIO',
 FECHMODIF        IS  'FECHA_MODIF',
 HORAMODIF        IS  'HORA_MODIF',
 ESTADO           IS  'ESTADO_ACTUAL',
 CORREO_USU       IS  'CORREO_USUARIO',
 DETALL_ACC       IS  'DETALLE_ACCION'
);
