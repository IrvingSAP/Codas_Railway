-- *?************************************************************************
-- *  Programa:?SEGFFIFSLD                                                  *
-- *  Descripcion:Log de ejecuciones De proceso de depuracion Rutas       ?*
Create OR REPLACE Table &LIB/SEGFFIFSLD
(ID_LOG  INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY
            (START WITH 1, INCREMENT BY 1, NO CACHE),
 APLICATIVO CHAR (3)     NOT NULL DEFAULT '' ,
 PROCESO    CHAR (10)    NOT NULL DEFAULT '' ,
 CODFREQ    CHAR (1)     NOT NULL DEFAULT '' ,
 DIAFREQ    CHAR (4)     NOT NULL DEFAULT '' ,
 HORADEP    NUMERIC (4,2)  NOT NULL DEFAULT 0  ,
 ARCHIVO    CHAR (50)    NOT NULL DEFAULT '' ,
 NRDIAS     NUMERIC (5)  NOT NULL DEFAULT 0  ,
 NROSQN     NUMERIC (9)  NOT NULL DEFAULT 0  ,
 IFSDEP     CHAR (250)   NOT NULL DEFAULT '' ,
 ARCDEP     CHAR (250)   NOT NULL DEFAULT '' ,
 TEXTO      VARCHAR (300) NOT NULL DEFAULT '' ,
 FECHA      TIMESTAMP    NOT NULL DEFAULT CURRENT TIMESTAMP,
 TRABAJO    CHAR (30)    NOT NULL DEFAULT '' ,
 MSGDEP     CHAR    (7)  NOT NULL DEFAULT '' ,
 NOMSAV     CHAR (10)    NOT NULL DEFAULT '' ,
 LIBSAV     CHAR (10)    NOT NULL DEFAULT '' ,
 OWNDEP     CHAR (10)    NOT NULL DEFAULT '' ,
 CONSTRAINT SEGFFIFSLD_PK PRIMARY KEY(ID_LOG, APLICATIVO, PROCESO)
) RcdFmt @RIFSLG;

Label On Table &LIB/SEGFFIFSLD Is 'Log proceso de depuracion de rutas IFS';

Label On  &LIB/SEGFFIFSLD
(ID_LOG        IS   'CLAVE INICA',
 APLICATIVO    Is   'Aplicativo' ,
 PROCESO       Is   'Id de Proceso' ,
 CODFREQ       Is   'Código frecuencia',
 DIAFREQ       Is   'Día frecuencia',
 HORADEP       Is   'Hora depuración',
 ARCHIVO       Is   'Archivo ó patrón',
 NRDIAS        Is   'Días Antiguedad',
 NROSQN        Is   'Secuencia',
 IFSDEP        Is   'Ruta IFS depurada',
 ARCDEP        Is   'Archivo depurado',
 MSGDEP        Is   'Mensaje LOG',
 TEXTO         Is   'Texto LOG',
 TRABAJO       Is   'Trabajo',
 FECHA         Is   'Fecha Depuración',
 NOMSAV        Is   'Nombre Archivo Salvado',
 LIBSAV        Is   'Librería Archivo Salvado',
 OWNDEP        Is   'Propietario a depurar'
 );

Label On Column &LIB/SEGFFIFSLD
(ID_LOG        TEXT IS   'CLAVE INICA',
 APLICATIVO    Text Is   'Aplicativo' ,
 PROCESO       Text Is   'Id de Proceso' ,
 CODFREQ       Text Is   'Código frecuencia',
 DIAFREQ       Text Is   'Día frecuencia',
 HORADEP       Text Is   'Hora depuración',
 ARCHIVO       Text Is   'Archivo ó patrón',
 NRDIAS        Text Is   'Días Antiguedad',
 NROSQN        Text Is   'Secuencia',
 IFSDEP        Text Is   'Ruta IFS depurada',
 ARCDEP        Text Is   'Archivo depurado',
 MSGDEP        Text Is   'Mensaje LOG',
 TEXTO         Text Is   'Texto LOG',
 TRABAJO       Text Is   'Trabajo',
 FECHA         Text Is   'Fecha Depuración',
 NOMSAV        Text Is   'Nombre Archivo Salvado',
 LIBSAV        Text Is   'Librería Archivo Salvado',
 OWNDEP        Text Is   'Propietario a depurar'
 );
