--------------------------------------------------------------------------------
-- TABLA    : &LIB/SEGTBRLTST
-- OBJETIVO : LOG DE CREACION AUTOMATICA DE USUARIOS
-- FECHA    : OCTUBRE 20 - 2019
-- AUTOR    : ANDRES CUARTAS - ACCENTURE
--------------------------------------------------------------------------------

-- Creando la tabla &LIB/SEGTBRLTST
CREATE OR REPLACE TABLE &LIB/SEGTBRLTST(
   ACCION CHARACTER ( 10 ) ,
   USUARIO CHARACTER ( 10 ),
   FECHA  timestamp,
   DATOS CHARACTER (200))
   RCDFMT RLTST;

-- Estableciendo el texto de etiqueta para &LIB/CTRFFOWNLG
LABEL ON TABLE &LIB/SEGTBRLTST
   IS 'Tabla LOG de mantenimiento reglas';

-- Estableciendo las etiquetas de columna para &LIB/CTRFFOWNLG
LABEL ON COLUMN &LIB/SEGTBRLTST(
   ACCION TEXT IS 'Accion',
   USUARIO TEXT IS 'Usuario',
   FECHA TEXT IS 'Fecha'  ,
   DATOS   TEXT IS 'Datos');

-- Estableciendo las cabeceras de columna para &LIB/CTRFFOWNLG
LABEL ON COLUMN &LIB/SEGTBRLTST(
   ACCION IS 'Accion',
   USUARIO IS 'Usuario',
   FECHA IS 'Fecha'  ,
   DATOS   IS 'Datos');
