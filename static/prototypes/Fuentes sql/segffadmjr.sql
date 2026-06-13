CREATE OR REPLACE TABLE &LIB/SEGFFADMJR (
JOURNAL      CHAR       (10)    ,
LIBJRN       CHAR       (10)    ,
CAMBIARCV    CHAR       (3 )    ,
ELIMINARCV   CHAR       (3 )    ,
PROCESO      CHAR       (10)    ,
ESTADO       CHAR       (1 )    ,
USUCREA      CHAR       (10)    ,
FECCREA      TIMESTAMP          ,
USUMODIF     CHAR       (10)    ,
FECMODIF     TIMESTAMP          ,
ELIRCVSV     CHAR       (1) DEFAULT 'S',
CANTIDAD     NUMERIC    (3) DEFAULT 1,
CONSTRAINT PK_ADMJR PRIMARY KEY (JOURNAL, LIBJRN))
RCDFMT   REGADMJR;

LABEL ON TABLE &LIB/SEGFFADMJR  Is
'Registro administradror JRN';

LABEL ON &LIB/SEGFFADMJR (
Journal       Text Is  'Journal',
Libjrn        Text Is  'Lib Jrn',
CambiaRcv     Text Is  'Cambia Rcv',
EliminaRcv    Text Is  'Elimina Rcv',
ELIRCVSV      TEXT IS  'ELIMINA RCV SAV',
CANTIDAD      TEXT IS  'CANT. NO BORRAR',
Estado        Text Is  'Estado',
Proceso       Text Is  'Proceso',
UsuCrea       Text Is  'Usuario Crea',
FecCrea       Text Is  'Fecha Crea',
UsuModif      Text Is  'Usuario Modifica',
FecModif      Text Is  'Fecha Modificación');


LABEL ON COLUMN &LIB/SEGFFADMJR (
Journal            Is  'Journal',
Libjrn             Is  'Lib Jrn',
CambiaRcv          Is  'Cambia Rcv',
EliminaRcv         Is  'Elimina Rcv',
Estado             Is  'Estado',
ELIRCVSV           IS  'ELIMINA RCV SAV',
CANTIDAD           IS  'CANT. NO BORRAR',
Proceso            Is  'Proceso',
UsuCrea            Is  'Usuario Crea',
FecCrea            Is  'Fecha Crea',
UsuModif           Is  'Usuario Modifica',
FecModif           Is  'Fecha Modificación');
