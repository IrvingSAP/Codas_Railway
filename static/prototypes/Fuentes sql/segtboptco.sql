-------------------------------------------------------------------------------
-- TABLA    : &LIB/SEGTBOPTCO
-- OBJETIVO : Tabla con resultado de usuarios optima y confianza
-- FECHA    : Julio - 2020
-- AUTOR    : Cristhian Herrera - Bancolombia
--------------------------------------------------------------------------------

-- Creando la tabla &LIB/SEGTBOPTCO
CREATE OR REPLACE TABLE &LIB/SEGTBOPTCO (
   CODIGO_PK INTEGER IMPLICITLY HIDDEN GENERATED ALWAYS AS IDENTITY,
   BIBLIOTECA CHARACTER ( 10 ) ,
   USUARIO CHARACTER ( 10 ) ,
   GRUPO   CHARACTER ( 10 ),
   NOMBRE  CHARACTER ( 30 ))
   RCDFMT OPTCON;

-- Estableciendo eL texto de etiqueta para &LIB/SEGTBUSRPE
LABEL ON TABLE &LIB/SEGTBOPTCO
   IS 'Tabla informe usuarios Optima y Confianza';

