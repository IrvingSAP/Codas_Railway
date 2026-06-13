Create Table &LIB/SEGFFDAMIE
(APLICATIVO CHAR (3)     NOT NULL DEFAULT '' ,
 PROCESO    CHAR (10)    NOT NULL DEFAULT '' ,
 BIBLIOTECA CHAR (10)    NOT NULL DEFAULT '' ,
 ARCHIVO    CHAR (10)    NOT NULL DEFAULT '' ,
 MIEMBRO    CHAR (10)    NOT NULL DEFAULT '' ,
 ESTADO     CHAR (1)     NOT NULL DEFAULT '' ,
 FECCRE     TIMESTAMP    NOT NULL DEFAULT CURRENT TIMESTAMP,
 USUCRE     CHAR (10)    NOT NULL DEFAULT '' ,
 FECMOD     TIMESTAMP    NOT NULL DEFAULT CURRENT TIMESTAMP,
 USUMOD     CHAR (10)    NOT NULL DEFAULT '' ,
 TIPSQN     NUMERIC(2)   NOT NULL DEFAULT 0  ,
 CANDIG     NUMERIC(1)   NOT NULL DEFAULT 0  ,
 NDESDE     NUMERIC(9)   NOT NULL DEFAULT 0  ,
 NHASTA     NUMERIC(9)   NOT NULL DEFAULT 0  ,
 FECSIG     NUMERIC(8)   NOT NULL DEFAULT 0  ,
 Constraint SEGFFDAMIE_PK Primary Key(APLICATIVO, PROCESO,
                                      BIBLIOTECA, ARCHIVO, MIEMBRO)
) RcdFmt @RDAMIE;

Label On Table &LIB/SEGFFDAMIE Is 'Depuración de miembros';

Label On Column  &LIB/SEGFFDAMIE
(APLICATIVO    Is     'Código              aplicativo',
 PROCESO       Is     'Id                  proceso' ,
 BIBLIOTECA    Is     'Biblioteca' ,
 ARCHIVO       Is     'Archivo             físico' ,
 MIEMBRO       Is     'Miembro' ,
 ESTADO        Is     'Estado              Registro' ,
 FECCRE        Is     'Fecha/hora          creación',
 USUCRE        Is     'Usuario             creación',
 FECMOD        Is     'Fecha/hora          modificación',
 USUMOD        Is     'Usuario             modificación',
 TIPSQN        Is     'Tipo                Secuencia',
 CANDIG        Is     'Cantidad            Digitos',
 NDESDE        Is     'Numero              Desde',
 NHASTA        Is     'Numero              Hasta',
 FECSIG        Is     'Fecha               Siguiente'
 );

Label On Column &LIB/SEGFFDAMIE
(APLICATIVO    Text Is   'Aplicativo' ,
 PROCESO       Text Is   'Id de Proceso' ,
 BIBLIOTECA    Text Is   'Biblioteca' ,
 ARCHIVO       Text Is   'Archivo físico' ,
 MIEMBRO       Text Is   'Miembro' ,
 ESTADO        Text Is   'Estado A=Activo, I=Inactivo' ,
 FECCRE        Text Is   'Fecha/hora creación',
 USUCRE        Text Is   'Usuario creación',
 FECMOD        Text Is   'Fecha/hora modificación',
 USUMOD        Text Is   'Usuario modificación',
 TIPSQN        Text Is   'Tipo Secuencia',
 CANDIG        Text Is   'Cantidad Digitos',
 NDESDE        Text Is   'Numero Desde',
 NHASTA        Text Is   'Numero Hasta',
 FECSIG        Text Is   'Fecha Siguiente'
 );
