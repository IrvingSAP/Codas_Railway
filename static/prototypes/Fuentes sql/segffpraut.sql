-- *?************************************************************************
-- *  Programa:?SEGFFPRAUT                                                  *
-- *  Descripcion:Componente Autorizador Tabla de Parametrizacion de      ?*
-- *              Objetos a Autorizar                                     ?*
-- *                                                                       ?*
-- *  Autor:?Rigoberto Ríos Bola¦os                                         *
-- *  Empresa:?PersonalSoft S.A.S                                           *
-- *  Fecha Creacion:?24 - Mayo  2011                                       *
-- *?************************************************************************
-- *  Modificaciones:                                                     ?*
-- *                                                                      ?*
-- *                                                                      ?*
-- *                                                                        *
-- *  Autor:?Nnnnnnnnnnn Nnnnnnnnnnnnn                                      *
-- *  Empresa:?PersonalSoft S.A.                                            *
-- *  Fecha Modificación:?DD - MMM - AAAA                                   *
-- *?************************************************************************
Drop Table &LIB/SEGFFPRAUT;
Create Table &LIB/SEGFFPRAUT
(AUCLAVE    CHAR (26) NOT NULL DEFAULT ''
,AUPROCESO  CHAR (10) NOT NULL DEFAULT ''
,AUCODAUTO  CHAR (13) NOT NULL DEFAULT ''
,AUOBJETO   CHAR (20) NOT NULL DEFAULT ''
,AURUTAIFS  CHAR (60) NOT NULL DEFAULT ''
,AUFECCRE   DEC  (8, 0)  NOT NULL DEFAULT 0
,AUHORCRE   DEC  (6, 0)  NOT NULL DEFAULT 0
,AUUSRCRE   CHAR (10) NOT NULL DEFAULT ''
,AUFECMOD   DEC  (8, 0)  NOT NULL DEFAULT 0
,AUHORMOD   DEC  (6, 0)  NOT NULL DEFAULT 0
,AUUSRMOD   CHAR (10) NOT NULL DEFAULT ''
,Constraint SEGFFPRAUT_PK Primary Key(AUCLAVE)
) RcdFmt PrAutReg ;

Label On Table &LIB/SEGFFPRAUT Is 'Parametrizacion de Objetos Autorizar.';
Label On  &LIB/SEGFFPRAUT
(AUCLAVE       Text Is 'Clave Unica'
,AUPROCESO     Text Is 'Nombre del Proceso'
,AUCODAUTO     Text Is 'Código de Autorización'
,AUOBJETO      Text Is 'Objeto'
,AURUTAIFS     Text Is 'Ruta IFS a Autorizar'
,AUFECCRE      Text Is 'Fecha de Creación (del registro)'
,AUHORCRE      Text Is 'Hora de Creación (del registro)'
,AUUSRCRE      Text Is 'Usuario de Creación (del registro)'
,AUFECMOD      Text Is 'Fecha de Modificación (del registro)'
,AUHORMOD      Text Is 'Hora de Modificación (del registro)'
,AUUSRMOD      Text Is 'Usuario de Modificación (del registro)'
 );

Label On Column &LIB/SEGFFPRAUT
(AUCLAVE            Is 'Clave Unica'
,AUPROCESO          Is 'Nombre del Proceso'
,AUCODAUTO          Is 'Código de Autorización'
,AUOBJETO           Is 'Objeto'
,AURUTAIFS          Is 'Ruta IFS a Autorizar'
,AUFECCRE           Is 'Fecha de Creación (del registro)'
,AUHORCRE           Is 'Hora de Creación (del registro)'
,AUUSRCRE           Is 'Usuario de Creación (del registro)'
,AUFECMOD           Is 'Fecha de Modificación (del registro)'
,AUHORMOD           Is 'Hora de Modificación (del registro)'
,AUUSRMOD           Is 'Usuario de Modificación (del registro)'
 );
