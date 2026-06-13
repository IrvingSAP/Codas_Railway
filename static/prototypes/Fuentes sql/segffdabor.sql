Create Table &LIB/SEGFFDABOR
(APLICATIVO CHAR (3)     NOT NULL DEFAULT '' ,
 PROCESO    CHAR (10)    NOT NULL DEFAULT '' ,
 BIBLIOTECA CHAR (10)    NOT NULL DEFAULT '' ,
 ARCHIVO    CHAR (10)    NOT NULL DEFAULT '' ,
 ESTADO     CHAR (1)     NOT NULL DEFAULT '' ,
 FECCRE     TIMESTAMP    NOT NULL DEFAULT CURRENT TIMESTAMP,
 USUCRE     CHAR (10)    NOT NULL DEFAULT '' ,
 FECMOD     TIMESTAMP    NOT NULL DEFAULT CURRENT TIMESTAMP,
 USUMOD     CHAR (10)    NOT NULL DEFAULT '',
 Constraint SEGFFDABOR_PK Primary Key(APLICATIVO, PROCESO,
                                      BIBLIOTECA, ARCHIVO)
) RcdFmt @RDABOR;

Label On Table &LIB/SEGFFDABOR Is 'Tabla de depur borrado de archivos';

Label On Column  &LIB/SEGFFDABOR
(APLICATIVO    Is     'Código              aplicativo',
 PROCESO       Is     'Id                  proceso' ,
 BIBLIOTECA    Is     'Biblioteca' ,
 ARCHIVO       Is     'Archivo             físico' ,
 ESTADO        Is     'Estado              Registro' ,
 FECCRE        Is     'Fecha/hora          creación',
 USUCRE        Is     'Usuario             creación',
 FECMOD        Is     'Fecha/hora          modificación',
 USUMOD        Is     'Usuario             modificación'
 );

Label On Column &LIB/SEGFFDABOR
(APLICATIVO    Text Is   'Aplicativo' ,
 PROCESO       Text Is   'Id de Proceso' ,
 BIBLIOTECA    Text Is   'Biblioteca' ,
 ARCHIVO       Text Is   'Archivo físico' ,
 ESTADO        Text Is   'Estado A=Activo, I=Inactivo' ,
 FECCRE        Text Is   'Fecha/hora creación',
 USUCRE        Text Is   'Usuario creación',
 FECMOD        Text Is   'Fecha/hora modificación',
 USUMOD        Text Is   'Usuario modificación'
 );
