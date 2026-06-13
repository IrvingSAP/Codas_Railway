CREATE TABLE &LIB/SEGFFTRPAR (
TRPCODIGO  Char       (10)    ,
TRPDESCOD  VarChar    (50)    ,
TRPESTADO  Char       (01)    ,
TRPVALOR   Char       (10)    ,
TRPDESVLR  VarChar    (50)    ,
TRPESTVLR  Char       (01)    ,
TRPUSUCRE  Char       (10)    ,
TRPFECCRE  TimeStamp          ,
TRPUSUMOD  Char       (10)    ,
TRPFECMOD  TimeStamp          ,
CONSTRAINT PK_TRPAR PRIMARY KEY (TRPCODIGO, TRPVALOR))
RCDFMT   REGTRPAR;

LABEL ON TABLE &LIB/SEGFFTRPAR  Is
'Parametros Generales - Componentes Transversales';

LABEL ON &LIB/SEGFFTRPAR (
TRPCODIGO  Text Is  'Codigo del Parametro',
TRPDESCOD  Text Is  'Descripcion',
TRPESTADO  Text Is  'Estado',
TRPVALOR   Text Is  'Codigo del Valor General',
TRPDESVLR  Text Is  'Descripcion Valor',
TRPESTVLR  Text Is  'Estado Valor',
TRPUSUCRE  Text Is  'Usuario Creación',
TRPFECCRE  Text Is  'Fecha Creación',
TRPUSUMOD  Text Is  'Usuario Cambio',
TRPFECMOD  Text Is  'Fecha Cambio');

LABEL ON COLUMN &LIB/SEGFFTRPAR (
TRPCODIGO  Is  'Codigo del Parametro',
TRPDESCOD  Is  'Descripcion',
TRPESTADO  Is  'Estado',
TRPVALOR   Is  'Codigo del Valor General',
TRPDESVLR  Is  'Descripcion Valor',
TRPESTVLR  Is  'Estado Valor',
TRPUSUCRE  Is  'Usuario Creación',
TRPFECCRE  Is  'Fecha Creación',
TRPUSUMOD  Is  'Usuario Cambio',
TRPFECMOD  Is  'Fecha Cambio');
