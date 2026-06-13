-------------------------------------------------------------------
 SCRIPT....: SEGTBCSGCU                                          --
on.........: Seg-Tablas  Consulta Generica, Control Usuarios     --
             Autorizadores                                       --
to.........: TABLE                                               --
Creacion...: Julio - 2024                                        --
...........: Steven Perez                                        --
-------------------------------------------------------------------
s Tablas  Maestro de Novedades
R REPLACE  &LIB/SEGTBCSGCU
PLACE TABLE &LIB.CON_GEN_USU_AUTORIZADORES
       FOR SYSTEM NAME SEGTBCSGCU(
RIZADOR         FOR COLUMN USUARIOA CHAR(10)
                NOT NULL DEFAULT '' CCSID 284 ,
IZADOR          FOR COLUMN ESTADOA CHAR(1)
                NOT NULL DEFAULT '' CCSID 284 ,
ESO             FOR COLUMN USUARIOIN CHAR(10)
                NOT NULL DEFAULT '' CCSID 284 ,
O               FOR COLUMN FECHAIN DATE
                NOT NULL DEFAULT CURRENT DATE,
                FOR COLUMN HORAIN TIME
                NOT NULL DEFAULT CURRENT TIME ,
ALIZA           FOR COLUMN USUARIOAC CHAR(10)
                NOT NULL DEFAULT '' CCSID 284 ,
IZA             FOR COLUMN FECHAAC DATE
                NOT NULL DEFAULT CURRENT DATE,
ZA              FOR COLUMN HORAAC TIME
                NOT NULL DEFAULT CURRENT TIME,

maria
LIB.USUARIO_AUTORIZADOR_PK
(USUARIO_AUTORIZADOR))
GCU;


ÓN */
LE &LIB.CON_GEN_USU_AUTORIZADORES IS
arios Autorizadores - Consulta Generica' ;

B.CON_GEN_USU_AUTORIZADORES(
RIZADOR       TEXT Is 'USUARIO_AUTORIZADOR',
IZADOR        TEXT Is 'ESTADO_AUTORIZADOR',
ESO           TEXT Is 'USUARIO_INGRESO',
O             TEXT Is 'FECHA_INGRESO',
              TEXT Is 'HORA_INGRESO',
ALIZA         TEXT Is 'USUARIO_ACTUALIZA',
IZA           TEXT Is 'FECHA_ACTUALIZA',
ZA            TEXT Is 'HORA_ACTUALIZA');

