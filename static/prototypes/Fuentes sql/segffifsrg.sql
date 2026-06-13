-- *?************************************************************************
-- *  Programa:?SEGFFIFSRG                                                  *
-- *  Descripcion:Log de ejecuciones De proceso de depuracion Rutas       ?*
Create OR REPLACE Table &LIB/SEGFFIFSRG (
 APLICATIVO        CHAR         (3)   NOT NULL DEFAULT '' ,
 PROCESO           CHAR        (10)   NOT NULL DEFAULT '' ,
 ARCHIVO           CHAR        (50)   NOT NULL DEFAULT '' ,
 NRDIAS            NUMERIC     (5,0)  NOT NULL DEFAULT 0 ,
 ESTADO            CHAR         (1)   NOT NULL DEFAULT '' ,
 OWNDEP            CHAR        (10)   NOT NULL DEFAULT '' ,
 FECCRE            TIMESTAMP          NOT NULL DEFAULT CURRENT TIMESTAMP,
 USUCRE            CHAR         (10)  NOT NULL DEFAULT '' ,
 FECMOD            TIMESTAMP          NOT NULL DEFAULT CURRENT TIMESTAMP,
 USUMOD            CHAR         (10)  NOT NULL DEFAULT '' ,
 Constraint SEGFFIFSRG_PK Primary Key(APLICATIVO, PROCESO,ARCHIVO)
) RcdFmt @RIFSRG;

Label On Table &LIB/SEGFFIFSRG Is 'Archivos depuracion de Rutas IFS';

Label On  &LIB/SEGFFIFSRG
(APLICATIVO    Is     'Código              Aplicativo' ,
 PROCESO       Is     'Id                  proceso' ,
 ARCHIVO       Is     'Archivo ó           patrón' ,
 NRDIAS        Is     'Días                antiguedad' ,
 ESTADO        Is     'Estado                        ' ,
 OWNDEP        Is     'Propietario a       Depurar' ,
 FECCRE        Is     'Fecha/hora          creación',
 USUCRE        Is     'Usuario             creación',
 FECMOD        Is     'Fecha/hora          modificación',
 USUMOD        Is     'Usuario             modificación'
 );

Label On Column &LIB/SEGFFIFSRG
(APLICATIVO    Text Is   'Aplicativo' ,
 PROCESO       Text Is   'Poceso' ,
 ARCHIVO       Text Is   'Archivo ó patrón' ,
 NRDIAS        Text Is   'Días antiguedad' ,
 ESTADO        Text Is   'Estado' ,
 OWNDEP        Text Is   'Propietario a Depurar' ,
 FECCRE        Text Is   'Fecha/hora creación',
 USUCRE        Text Is   'Usuario creación',
 FECMOD        Text Is   'Fecha modificación',
 USUMOD        Text Is   'Usuario modificación'
 );
