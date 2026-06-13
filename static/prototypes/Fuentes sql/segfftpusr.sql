Create Table &LIB/SEGFFTPUSR
( NOMUSR     CHAR (10)    NOT NULL DEFAULT '' ,
  TIPOUSR1   CHAR (10)    NOT NULL DEFAULT '' ,
  TIPOUSR2   CHAR (10)    NOT NULL DEFAULT '' ,
  CAMPO1     NUMERIC(8)   NOT NULL DEFAULT 0 ,
  CAMPO2     NUMERIC(8)   NOT NULL DEFAULT 0 ,
  CAMPO3     CHAR(40)     NOT NULL DEFAULT ' ' ,
  CAMPO4     CHAR(10)     NOT NULL DEFAULT ' ' ,
  CAMPO5     CHAR(3)      NOT NULL DEFAULT ' ' ,
  CAMPO6     NUMERIC(5)   NOT NULL DEFAULT 0 ,
  FECHA      NUMERIC(8)   NOT NULL DEFAULT 0 ,
  HORA       NUMERIC(6)   NOT NULL DEFAULT 0 ,
  CONSTRAINT SEGFFPTUSR_PK PRIMARY KEY(NOMUSR) );

Label On Table &LIB/SEGFFTPUSR Is 'SEG - Tipos de Usuarios';

Label On Column  &LIB/SEGFFTPUSR
( NOMUSR        Is     'Nombre              usuario',
  TIPOUSR1      Is     'Tipo                (TEST/PROD)',
  TIPOUSR2      Is     'Subtipo             usuario',
  CAMPO1        Is     'Campo Uso           Futuro 1',
  CAMPO2        Is     'Campo Uso           Futuro 2',
  CAMPO3        Is     'Campo Uso           Futuro 3',
  CAMPO4        Is     'Campo Uso           Futuro 4',
  CAMPO5        Is     'Campo Uso           Futuro 5',
  CAMPO6        Is     'Campo Uso           Futuro 6',
  FECHA         Is     'Fecha               carga',
  HORA          Is     'Hora                carga' );

Label On Column &LIB/SEGFFTPUSR
( NOMUSR        Text Is   'Nombre biblioteca',
  TIPOUSR1      Text Is   'Tipo (TEST/PROD)',
  TIPOUSR2      Text Is   'Subtipo',
  CAMPO1        Text Is   'Campo Uso Futuro 1',
  CAMPO2        Text Is   'Campo Uso Futuro 2',
  CAMPO3        Text Is   'Campo Uso Futuro 3',
  CAMPO4        Text Is   'Campo Uso Futuro 4',
  CAMPO5        Text Is   'Campo Uso Futuro 5',
  CAMPO6        Text Is   'Campo Uso Futuro 6',
  FECHA         Text Is   'Fecha carga',
  HORA          Text Is   'Hora carga' );
