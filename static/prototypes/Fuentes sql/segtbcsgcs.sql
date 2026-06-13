-------------------------------------------------------------------
 SCRIPT....: SEGTBCSGCS                                         --
on.........: Seg-Tablas  Consulta Generica, seleccion de campos --
to.........: TABLE                                              --
Creacion...: Julio - 2024                                        --
...........: Irving Sifuntes                                    --
-------------------------------------------------------------------
s Tablas  Maestro de Novedades
R REPLACE  &LIB/SEGTBCSGCS
PLACE TABLE &LIB.CON_GEN_SEL_CAMPOS
       FOR SYSTEM NAME SEGTBCSGCS(
IO              FOR COLUMN USUARIO CHAR(10)
                NOT NULL DEFAULT '' CCSID 284 ,
RIA             FOR COLUMN LIBRERIA CHAR(10)
                NOT NULL DEFAULT '' CCSID 284 ,
VO              FOR COLUMN ARCHIVO CHAR(10)
                NOT NULL DEFAULT '' CCSID 284 ,
                FOR COLUMN NOMCAMPO CHAR(10)
                NOT NULL DEFAULT '' CCSID 284 ,
                FOR COLUMN TPOCAMPO CHAR(10)
                NOT NULL DEFAULT '' CCSID 284 ,
ERO             FOR COLUMN LENTERO NUMERIC(5)
                NOT NULL DEFAULT 0  ,
IMAL            FOR COLUMN LDECIMAL NUMERIC(2)
                NOT NULL DEFAULT 0  ,
PCION           FOR COLUMN DESCAMPO CHAR(100)
                NOT NULL DEFAULT '' CCSID 284 ,
ION             FOR COLUMN SELCAMPO CHAR(01)
                NOT NULL DEFAULT '' CCSID 284 ,
maria
LIB.NOMBRE_USUARIO_PK
( NOMBRE_USUARIO, NOMBRE_LIBRERIA, NOMBRE_ARCHIVO,
 ))
BCGES;


ÓN */
LE &LIB.CON_GEN_SEL_CAMPOS IS
nerica Seleccion de Campos' ;

B.CON_GEN_SEL_CAMPOS(
IO            TEXT Is 'NOMBRE_USUARIO',
RIA           TEXT Is 'NOMBRE_LIBRERIA',
VO            TEXT Is 'NOMBRE_ARCHIVO',
              TEXT Is 'NOMBRE_CAMPO',
              TEXT Is 'TIPO_CAMPO',
ERO           TEXT Is 'LONGITUD_ENTERO',
IMAL          TEXT Is 'LONGITUD_DECIMAL',
PCION         TEXT Is 'CAMPO_DESCRIPCION',
ION           TEXT Is 'CAMPO_SELECCION');
