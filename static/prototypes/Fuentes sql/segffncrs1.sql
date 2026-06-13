-- *?************************************************************************
-- *  Programa:?SEGFFNCRS1
-- *  Descripcion:LOG NROS DE CELULAR PARA CONSULTA DE REEXP SIMCARD      ?*
-- *                                                                       ?*
-- *  Autor:?WILLIAM GONZALEZ R                                             *
-- *  Empresa:?SOPHOS SOLUTIONS                                             *
-- *  Fecha Creacion:?24 - MARZO 2022.                                      *
-- *?************************************************************************
-- *  Modificaciones:                                                     ?*
-- *                                                                      ?*
-- *                                                                      ?*
-- *                                                                        *
-- *  Autor:?XXXXXXXXXXX XXXXXXXXXXXXX                                      *
-- *  Empresa:?XXXXXXXXXXXXXXXX.                                            *
-- *  Fecha Modificación:?DD - MMM - AAAA                                   *
-- *?************************************************************************

        CREATE OR REPLACE TABLE  &LIB/SEGFFNCRS1
        (
          CLAVEUNICA CHARACTER(26) NOT NULL WITH DEFAULT,
          NROCELULAR CHARACTER(15) NOT NULL WITH DEFAULT,
          FECHANTCON NUMERIC(8,0) NOT NULL WITH DEFAULT,
          HORAANTCON NUMERIC(6,0) NOT NULL WITH DEFAULT,
          FECHDESCON NUMERIC(8,0) NOT NULL WITH DEFAULT,
          HORADESCON NUMERIC(6,0) NOT NULL WITH DEFAULT,
          TIEMPOTRAN NUMERIC(8,0) NOT NULL WITH DEFAULT,
          DTAATRNSEG NUMERIC(8,0) NOT NULL WITH DEFAULT,
          DTAAINTTMP NUMERIC(8,0) NOT NULL WITH DEFAULT,
          DTAAMAXLEC NUMERIC(8,0) NOT NULL WITH DEFAULT
        ) RCDFMT PRAUTREG;

        -- *- DESCRIPCIÓN ----------------------------------------
        LABEL ON TABLE &LIB/SEGFFNCRS1 IS 'LOG REEXPEDICION DE SIM CARD';

        LABEL ON  COLUMN &LIB/SEGFFNCRS1 (
          CLAVEUNICA IS 'CLAVE UNICA',
          NROCELULAR IS 'NRO CELULAR',
          FECHANTCON IS 'FECHA ANTES DE CONSULTA',
          HORAANTCON Is 'HORA ANTES DE CONSULTA',
          FECHDESCON Is 'FECHA DESPUES DE CONSULTA',
          HORADESCON Is 'HORA DESPUES DE CONSULTA',
          TIEMPOTRAN Is 'TIEMPO TRANSCURRIDO CONSULTA',
          DTAATRNSEG Is 'DTAARA TRANSACCIONX SEGUNDO',
          DTAAINTTMP Is 'DTAARA INTERVALO DE LECTURA',
          DTAAMAXLEC Is 'DTAARA MAX REGISTROS INTERVALO'
        );

        LABEL ON  COLUMN  &LIB/SEGFFNCRS1 (
          CLAVEUNICA    TEXT IS 'CLAVE UNICA',
          NROCELULAR    TEXT IS 'NRO CELULAR',
          FECHANTCON    TEXT IS 'FECHA ANTES DE CONSULTA',
          HORAANTCON    Text Is 'HORA ANTES DE CONSULTA',
          FECHDESCON    Text Is 'FECHA DESPUES DE CONSULTA',
          HORADESCON    Text Is 'HORA DESPUES DE CONSULTA',
          TIEMPOTRAN    Text Is 'TIEMPO TRANSCURRIDO CONSULTA',
          DTAATRNSEG    Text Is 'DTAARA TRANSACCIONX SEGUNDO',
          DTAAINTTMP    Text Is 'DTAARA INTERVALO DE LECTURA',
          DTAAMAXLEC    Text Is 'DTAARA MAX REGISTROS INTERVALO'
        );
