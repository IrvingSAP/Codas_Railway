Create Table &LIB/SEGFFTPLIB
( NOMLIB     CHAR (10)    NOT NULL DEFAULT '' ,
  TIPOLIB    CHAR (10)    NOT NULL DEFAULT '' ,
  CAMPO1     NUMERIC(8)   NOT NULL DEFAULT 0 ,
  CAMPO2     NUMERIC(8)   NOT NULL DEFAULT 0 ,
  CAMPO3     CHAR(40)     NOT NULL DEFAULT ' ' ,
  CAMPO4     CHAR(10)     NOT NULL DEFAULT ' ' ,
  CAMPO5     CHAR(3)      NOT NULL DEFAULT ' ' ,
  CAMPO6     NUMERIC(5)   NOT NULL DEFAULT 0 ,
  FECHA      NUMERIC(8)   NOT NULL DEFAULT 0 ,
  HORA       NUMERIC(6)   NOT NULL DEFAULT 0 ,
  Constraint SEGFFPTLIB_PK Primary Key(NOMLIB) );

Label On Table &LIB/SEGFFTPLIB Is 'SEG - Tipos de bibliotecas';

Label On Column  &LIB/SEGFFTPLIB
( NOMLIB        Is     'Nombre              biblioteca',
  TIPOLIB       Is     'Tipo                (TEST/PROD)',
  CAMPO1        Is     'Campo Uso           Futuro 1',
  CAMPO2        Is     'Campo Uso           Futuro 2',
  CAMPO3        Is     'Campo Uso           Futuro 3',
  CAMPO4        Is     'Campo Uso           Futuro 4',
  CAMPO5        Is     'Campo Uso           Futuro 5',
  CAMPO6        Is     'Campo Uso           Futuro 6',
  FECHA         Is     'Fecha               carga',
  HORA          Is     'Hora                carga' );

Label On Column &LIB/SEGFFTPLIB
( NOMLIB        Text Is   'Nombre biblioteca',
  TIPOLIB       Text Is   'Tipo (TEST/PROD)',
  CAMPO1        Text Is   'Campo Uso Futuro 1',
  CAMPO2        Text Is   'Campo Uso Futuro 2',
  CAMPO3        Text Is   'Campo Uso Futuro 3',
  CAMPO4        Text Is   'Campo Uso Futuro 4',
  CAMPO5        Text Is   'Campo Uso Futuro 5',
  CAMPO6        Text Is   'Campo Uso Futuro 6',
  FECHA         Text Is   'Fecha carga',
  HORA          Text Is   'Hora carga' );
