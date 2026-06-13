--------------------------------------------------------------------------------
-- TABLA    : &LIB/SEGVWDBLUS
-- OBJETIVO : VISTA PARA JOURNAL DE DESBLOQUEO DE USUARIOS
-- FECHA    : Agosto - 2020
-- AUTOR    : Cristhian Herrera - Bancolombia
--------------------------------------------------------------------------------

-- Creando la tabla &LIB/SEGVWDBLUS
 CREATE OR REPLACE VIEW &LIB.SEGVWDBLUS AS SELECT SEQUENCE_NUMBER,
 SUBSTR(CAST(PATH_NAME AS VARCHAR(100)),26) AS PN FROM
 TABLE(QSYS2.DISPLAY_JOURNAL('&LIB', 'SEGJRNDBL')) AS JT
 WHERE JOURNAL_ENTRY_TYPE = 'JT'

