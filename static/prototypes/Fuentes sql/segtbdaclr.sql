BC_1:"RUNSQLSTM SRCFILE(R1SEG/SEGSRC) SRCMBR(SEGTBDACLR) "
BC_2:"COMMIT(*NONE)"
OBJTYPE:"*FILE"
----------------------------------------------------------
 SCRIPT....: CREAR TABLA BASE.                          --
ÓN.........: TABLA DE Depuracion Archivo - CLRPFM       --
TO.........: TABLE                                      --
ENTO.......: EVC00032-TRANSVERSALES ISERIES.            --
O..........: TRANSVERSALES DE APOYO ISERIES.            --
CREACIÓN...: Agosto 2023                                --
...........: IRVING SIFUENTES                           --
ATOS RELACIONAL:  DB2 FOR I                             --
----------------------------------------------------------
IONES        :                                          --
MODIFICACIÓN :                                          --
...........  :                                          --
ÓN ......... :                                          --
ENTO.........:                                          --
----------------------------------------------------------

 LIBRERIA DE TRABAJO
T SCHEMA &LIB;

LA Control CLRPFM - Depuracion de Archivos
REPLACE TABLE &LIB/DEPURACION_ARCHIVO_CLRPFM
 NAME SEGTBDACLR(

 DE CAMPOS
IVO           FOR COLUMN APLICATIVO  CHAR(03)
              NOT NULL DEFAULT '' ,

              FOR COLUMN PROCESO     CHAR (10)
              NOT NULL DEFAULT '' ,

_OBJETO       FOR COLUMN BIBLIOTECA  CHAR (10)
              NOT NULL DEFAULT '' ,

PURAR         FOR COLUMN ARCHIVO     CHAR (10)
              NOT NULL DEFAULT '' ,

CESO          FOR COLUMN ESTADO      CHAR (01)
              NOT NULL DEFAULT '' ,

CION          FOR COLUMN FECCRE      TIMESTAMP
              NOT NULL DEFAULT CURRENT TIMESTAMP,

EACION        FOR COLUMN USUCRE      CHAR (10)
              NOT NULL DEFAULT '' ,

FICACION      FOR COLUMN FECMOD      TIMESTAMP
              NOT NULL DEFAULT CURRENT TIMESTAMP,

DIFICACION    FOR COLUMN USUMOD       CHAR (10)
              NOT NULL DEFAULT '',
IMARIA
 SEGTBDACLR_PK Primary Key(APLICATIVO, PROCESO,
               BIBLIOTECA, ARCHIVO)


EL REGISTRO
ACLR;

 DE LA TABLA

able &LIB/SEGTBDACLR Is
urador de Archivo Funcion CLRPFM';

N TABLE &LIB/SEGTBDACLR Is
urador de Archivo Funcion CLRPFM';

DE TEXTO DE LOS CAMPOS
olumn  &LIB/SEGTBDACLR
O   Is     'Código              aplicativo',
    Is     'Id                  proceso' ,
    Is     'Biblioteca          Objeto' ,
    Is     'Archivo             físico' ,
    Is     'Estado              Registro' ,
    Is     'Fecha/hora          creación',
    Is     'Usuario             creación',
    Is     'Fecha/hora          modificación',
    Is     'Usuario             modificación'


olumn &LIB/SEGTBDACLR
O   Text Is   'Aplicativo' ,
    Text Is   'Id de Proceso' ,
    Text Is   'Biblioteca de Objeto' ,
    Text Is   'Archivo físico' ,
    Text Is   'Estado A=Activo, I=Inactivo' ,
    Text Is   'Fecha/hora creación',
    Text Is   'Usuario creación',
    Text Is   'Fecha/hora modificación',
    Text Is   'Usuario modificación'


