-- *?************************************************************************
-- *  Programa:?SEGFFDEAUT                                                  *
-- *  Descripcion:Componente Autorizador Tabla de detalle de parametriza- ?*
-- *              cion de Objetos a Autorizar                             ?*
-- *                                                                       ?*
-- *  Autor:?Rigoberto Ríos Bola¦os                                         *
-- *  Empresa:?PersonalSoft S.A.S                                           *
-- *  Fecha Creacion:?25 - Mayo  2011                                       *
-- *?************************************************************************
-- *  Modificaciones:                                                     ?*
-- *                                                                      ?*
-- *                                                                      ?*
-- *                                                                        *
-- *  Autor:?Nnnnnnnnnnn Nnnnnnnnnnnnn                                      *
-- *  Empresa:?PersonalSoft S.A.                                            *
-- *  Fecha Modificación:?DD - MMM - AAAA                                   *
-- *?************************************************************************
Drop Table &LIB/SEGFFDEAUT;
Create Table &LIB/SEGFFDEAUT
(ADCLAVE    CHAR (26) NOT NULL DEFAULT ''
,ADUSUARIO  CHAR (10) NOT NULL DEFAULT ''
,ADPERMISOS CHAR (03) NOT NULL DEFAULT ''
,ADLSTAUT   CHAR (10) NOT NULL DEFAULT ''
,ADFECCRE   DEC  (8, 0)  NOT NULL DEFAULT 0
,ADHORCRE   DEC  (6, 0)  NOT NULL DEFAULT 0
,ADUSRCRE   CHAR (10) NOT NULL DEFAULT ''
,ADFECMOD   DEC  (8, 0)  NOT NULL DEFAULT 0
,ADHORMOD   DEC  (6, 0)  NOT NULL DEFAULT 0
,ADUSRMOD   CHAR (10) NOT NULL DEFAULT ''
,Constraint SEGFFDEAUT_PK Primary Key(ADCLAVE, ADUSUARIO, ADPERMISOS)
) RcdFmt DeAutReg ;

Label On Table &LIB/SEGFFDEAUT Is 'Parametriza. Detalle de Objetos Autorizar.';
Label On  &LIB/SEGFFDEAUT
(ADCLAVE       Text Is 'Clave Unica'
,ADUSUARIO     Text Is 'Usuario'
,ADPERMISOS    Text Is 'Permisos'
,ADLSTAUT      Text Is 'Lista de Autorizaciones'
,ADFECCRE      Text Is 'Fecha de Creación (del registro)'
,ADHORCRE      Text Is 'Hora de Creación (del registro)'
,ADUSRCRE      Text Is 'Usuario de Creación (del registro)'
,ADFECMOD      Text Is 'Fecha de Modificación (del registro)'
,ADHORMOD      Text Is 'Hora de Modificación (del registro)'
,ADUSRMOD      Text Is 'Usuario de Modificación (del registro)'
 );

Label On Column &LIB/SEGFFDEAUT
(ADCLAVE            Is 'Clave Unica'
,ADUSUARIO          Is 'Usuario'
,ADPERMISOS         Is 'Permisos'
,ADLSTAUT           Is 'Lista de Autorizaciones'
,ADFECCRE           Is 'Fecha de Creación (del registro)'
,ADHORCRE           Is 'Hora de Creación (del registro)'
,ADUSRCRE           Is 'Usuario de Creación (del registro)'
,ADFECMOD           Is 'Fecha de Modificación (del registro)'
,ADHORMOD           Is 'Hora de Modificación (del registro)'
,ADUSRMOD           Is 'Usuario de Modificación (del registro)'
 );
