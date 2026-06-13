Create Table &LIB/SEGFFDADAT
(APLICATIVO CHAR (3)     NOT NULL DEFAULT '' ,
 PROCESO    CHAR (10)    NOT NULL DEFAULT '' ,
 BIBLIOTECA CHAR (10)    NOT NULL DEFAULT '' ,
 ARCHIVO    CHAR (10)    NOT NULL DEFAULT '' ,
 CRITSELEC  CHAR (800)   NOT NULL DEFAULT '' ,
 ESTADO     CHAR (1)     NOT NULL DEFAULT '' ,
 FECCRE     TIMESTAMP    NOT NULL DEFAULT CURRENT TIMESTAMP,
 USUCRE     CHAR (10)    NOT NULL DEFAULT '' ,
 FECMOD     TIMESTAMP    NOT NULL DEFAULT CURRENT TIMESTAMP,
 USUMOD     CHAR (10)    NOT NULL DEFAULT '' ,
 RGZARCH    CHAR (1)     NOT NULL DEFAULT '' ,
 Constraint SEGFFDADAT_PK Primary Key(APLICATIVO, PROCESO,
                                      BIBLIOTECA, ARCHIVO)
) RcdFmt @RDADAT;

Label On Table &LIB/SEGFFDADAT Is 'Tabla de depuración de datos';

Label On Column  &LIB/SEGFFDADAT
(APLICATIVO    Is     'Código              aplicativo',
 PROCESO       Is     'Id                  proceso' ,
 BIBLIOTECA    Is     'Biblioteca' ,
 ARCHIVO       Is     'Archivo             físico' ,
 CRITSELEC     Is     'Criterio            Selección',
 ESTADO        Is     'Estado              Registro' ,
 FECCRE        Is     'Fecha/hora          creación',
 USUCRE        Is     'Usuario             creación',
 FECMOD        Is     'Fecha/hora          modificación',
 USUMOD        Is     'Usuario             modificación',
 RGZARCH       Is     'Reorganiza          archivo S/N'
 );

Label On Column &LIB/SEGFFDADAT
(APLICATIVO    Text Is   'Aplicativo' ,
 PROCESO       Text Is   'Id de Proceso' ,
 BIBLIOTECA    Text Is   'Biblioteca' ,
 ARCHIVO       Text Is   'Archivo físico' ,
 CRITSELEC     Text Is   'Criterio Selección',
 ESTADO        Text Is   'Estado A=Activo, I=Inactivo' ,
 FECCRE        Text Is   'Fecha/hora creación',
 USUCRE        Text Is   'Usuario creación',
 FECMOD        Text Is   'Fecha/hora modificación',
 USUMOD        Text Is   'Usuario modificación',
 RGZARCH       Text Is   'Reorganiza archivo S/N'
 );
