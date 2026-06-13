CREATE OR REPLACE TABLE &LIB/SEGFFASPER (
 USUARIO           CHAR        (10) NOT NULL DEFAULT '' ,
 CBANCO            CHAR        (3) NOT NULL DEFAULT '' ,
 CAPL              CHAR        (3) NOT NULL DEFAULT '' ,
 TMENU             CHAR        (2) NOT NULL DEFAULT '' ,
 SBMENU            CHAR        (2) NOT NULL DEFAULT '' ,
 OPCION            NUMERIC     (4) NOT NULL DEFAULT 0 ,
 ESTADO            CHAR        (1) NOT NULL DEFAULT '' ,
 FECHAP            NUMERIC     (8)   ,
 USERPRO           CHAR        (10)  ,
 FECHLOG           TIMESTAMP         ,
 DESCRIP           CHAR        (70) NOT NULL DEFAULT '',
 UFUNSI            char        (10) NOT NULL DEFAULT '',
 UPROGR            char        (10) NOT NULL DEFAULT ''
)
RCDFMT  RASPER;

LABEL ON TABLE &LIB/SEGFFASPER  Is
'USUARIOS PARA LA ASIGNACION DE PERMISOS';

LABEL ON &LIB/SEGFFASPER (
USUARIO            TEXT IS  'PERFIL USUARIO/ROL',
CBANCO             TEXT IS  'COD. BANCO',
CAPL               TEXT IS  'COD. APLICACION',
TMENU              TEXT IS  'TIPO DE MENU',
SBMENU             TEXT IS  'SUBTIPO DE MENU',
OPCION             TEXT IS  'OPCION DE MENU',
ESTADO             TEXT IS  'ESTADO',
FECHAP             TEXT IS  'FECHA SISTEMA',
USERPRO            TEXT IS  'USUARIO PROCESA',
FECHLOG            TEXT IS  'FECHA REGISTRO LOG',
DESCRIP            TEXT IS  'DESCRIPCION',
UFUNSI             TEXT IS  'FUNSION',
UPROGR             TEXT IS  'PROGRAMA');

LABEL ON COLUMN &LIB/SEGFFASPER (
USUARIO                 IS  'PERFIL USUARIO/ROL',
CBANCO                  IS  'COD. BANCO',
CAPL                    IS  'COD. APLICACION',
TMENU                   IS  'TIPO DE MENU',
SBMENU                  IS  'SUBTIPO DE MENU',
OPCION                  IS  'OPCION DE MENU',
ESTADO                  IS  'ESTADO',
FECHAP                  IS  'FECHA SISTEMA',
USERPRO                 IS  'USUARIO PROCESA',
FECHLOG                 IS  'FECHA REGISTRO LOG',
DESCRIP                 IS  'DESCRIPCION',
UFUNSI                  IS  'FUNSION',
UPROGR                  IS  'PROGRAMA');
