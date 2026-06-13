--------------------------------------------------------------------------------
-- TABLA    : &LIB/SEGTBIMPUS
-- OBJETIVO : Archivo Informe para CPYFRMSTR de IFS USM
-- FECHA    : Julio - 2020
-- AUTOR    : Cristhian Herrera - Bancolombia
--------------------------------------------------------------------------------

-- Creando la tabla &LIB/SEGTBIMPUS
CREATE OR REPLACE TABLE &LIB/SEGTBIMPUS (
   ID_USM  VARCHAR ( 10)  ,
   FECHA   VARCHAR ( 10)  ,
   USUARIO VARCHAR ( 10 ) ,
   IDENTIFICACION VARCHAR (15),
   PLATAFORMA      VARCHAR(20))
   RCDFMT FMTTBIMPUS;

-- Estableciendo eL texto de etiqueta para &LIB/SEGTBIMPUS
LABEL ON TABLE &LIB/SEGTBIMPUS
   IS 'Archivo Informe para CPYFRMSTR de IFS USM';

