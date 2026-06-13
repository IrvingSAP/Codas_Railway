-- *?************************************************************************
-- *  Programa:?SEGFFHSAUT                                                  *
-- *  Descripcion:Componente Autorizador                                  ?*
-- *              Archivo hisorico del LOG del componente Autorizador.    ?*
-- *              Almacena registro de entrada y de salida del componente.?*
-- *                                                                       ?*
-- *  Autor:?Rigoberto Ríos Bola¦os                                         *
-- *  Empresa:?PersonalSoft S.A.S                                           *
-- *  Fecha Creacion:?31 - Mayo  2011                                       *
-- *?************************************************************************
-- *  Modificaciones:                                                     ?*
-- *                                                                      ?*
-- *                                                                      ?*
-- *                                                                        *
-- *  Autor:?Nnnnnnnnnnn Nnnnnnnnnnnnn                                      *
-- *  Empresa:?PersonalSoft S.A.                                            *
-- *  Fecha Modificación:?DD - MMM - AAAA                                   *
-- *?************************************************************************
Drop Table &LIB/SEGFFHSAUT;
Create Table &LIB/SEGFFHSAUT
(LGFECHA    DEC  (8, 0)   NOT NULL DEFAULT 0
,LGHORA     DEC  (8, 0)   NOT NULL DEFAULT 0
,LGUSUARIO  CHAR (10)     NOT NULL DEFAULT ''
,LGNOMPROEJ CHAR (10)     NOT NULL DEFAULT ''
,LGNOMPROPR CHAR (10)     NOT NULL DEFAULT ''
,LGCODAUT   CHAR (13)     NOT NULL DEFAULT ''
,LGTIPREG   CHAR (1)      NOT NULL DEFAULT ''
,LGCODRES   CHAR (4)      NOT NULL DEFAULT ''
,LGDESRES   CHAR (70)     NOT NULL DEFAULT ''
,LGUSUAR1   CHAR (10)     NOT NULL DEFAULT ''
,LGUSUAR2   DEC  (15, 2)  NOT NULL DEFAULT 0
,LGUSUAR3   DEC  (17, 0)  NOT NULL DEFAULT 0
,LGUSUAR4   CHAR (20)     NOT NULL DEFAULT ''
) RcdFmt HSAutReg ;

Label On Table &LIB/SEGFFHSAUT Is 'Log del componente Autorizador.';
Label On  &LIB/SEGFFHSAUT
(LGFECHA       Text Is 'Fecha de registro'
,LGHORA        Text Is 'Hora de registro'
,LGUSUARIO     Text Is 'Usuario que ejecuta el proceso'
,LGNOMPROEJ    Text Is 'Nombre del proceso que ejecuta'
,LGNOMPROPR    Text Is 'Nombre del proceso parametrizado'
,LGCODAUT      Text Is 'Cód. autorización'
,LGTIPREG      Text Is 'Tipo de registro (E/S)'
,LGCODRES      Text Is 'Código de respuesta'
,LGDESRES      Text Is 'Descripción de Retorno'
,LGUSUAR1      Text Is 'Campo usuario 1'
,LGUSUAR2      Text Is 'Campo usuario 2'
,LGUSUAR3      Text Is 'Campo usuario 3'
,LGUSUAR4      Text Is 'Campo usuario 4'
 );

Label On Column &LIB/SEGFFHSAUT
(LGFECHA            Is 'Fecha de registro'
,LGHORA             Is 'Hora de registro'
,LGUSUARIO          Is 'Usuario que ejecuta el proceso'
,LGNOMPROEJ         Is 'Nombre del proceso que ejecuta'
,LGNOMPROPR         Is 'Nombre del proceso parametrizado'
,LGCODAUT           Is 'Cód. autorización'
,LGTIPREG           Is 'Tipo de registro (E/S)'
,LGCODRES           Is 'Código de respuesta'
,LGDESRES           Is 'Descripción de Retorno'
,LGUSUAR1           Is 'Campo usuario 1'
,LGUSUAR2           Is 'Campo usuario 2'
,LGUSUAR3           Is 'Campo usuario 3'
,LGUSUAR4           Is 'Campo usuario 4'
 );
