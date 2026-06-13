--------------------------------------------------------------------------------
-- TABLA    : &LIB/SEGTBLGCAU
-- OBJETIVO : LOG DE CREACION AUTOMATICA DE USUARIOS
-- FECHA    : OCTUBRE 20 - 2019
-- AUTOR    : ANDRES CUARTAS - ACCENTURE
--------------------------------------------------------------------------------

-- Creando la tabla &LIB/SEGTBLGCAU
CREATE OR REPLACE TABLE &LIB/SEGTBLGCAU (
   USMID CHARACTER ( 10 ) ,
   REGLA CHARACTER ( 10 ) ,
   ALERTA  CHARACTER ( 11 ) ,
   MENSAJE_LOG CHARACTER (200),
   FECHALOG TimeStamp)
   RCDFMT LGCAU;

-- Estableciendo el texto de etiqueta para &LIB/CTRFFOWNLG
LABEL ON TABLE &LIB/SEGTBLGCAU
   IS 'Log de creacion automatica de usuarios';

-- Estableciendo las etiquetas de columna para &LIB/CTRFFOWNLG
LABEL ON COLUMN &LIB/SEGTBLGCAU (
   USMID TEXT IS 'Pedido USM',
   REGLA TEXT IS 'Consecutivo regla',
   MENSAJE_LOG TEXT IS 'Mensaje del log',
   ALERTA TEXT IS 'Alertas',
   FECHALOG TEXT IS 'Fecha de novedad');

-- Estableciendo las cabeceras de columna para &LIB/CTRFFOWNLG
LABEL ON COLUMN &LIB/SEGTBLGCAU (
   USMID IS 'Pedido              USM                                     ',
   REGLA IS 'Consecutivo         Regla                                   ',
   ALERTA IS 'Alertas',
   MENSAJE_LOG IS 'Mensaje       del log                                 ',
   FECHALOG IS 'Fecha               novedad                                 ');
