--Tabla de Salida para Resumen por Objeto
--Cristhian Herrera Bancolombia 2020
CREATE OR REPLACE TABLE &LIB.SEGFFUSRP1(
BIBLIOTECA CHAR(10),
OBJETO CHAR(10),
TIPOOBJ CHAR(10),
OWNER CHAR(10),
AUTL  CHAR(10),
USUARIO CHAR(10),
PERMISO CHAR(10));

Label On Table &LIB.SEGFFUSRP1 Is 'Tabla Salida SEG Resumen por Objeto';
