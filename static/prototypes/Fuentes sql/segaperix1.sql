-- **************************************************************************
-- * ?Programa: SEGAPERIX1                                                  *
-- * ?Descripcion: Indice asignacion de autorizaciones masivas opciones de  *
-- *               menu                                                     *
-- * ?Autor: Pedro Rodriguez Pimienta - BANKVISION                          *
-- * ?Fecha Creacion: Junio / 2020                                          *
--  ******************************** *******   ******************************

  CREATE INDEX &LIB/SEGAPERIX1
     ON &LIB/SEGFFASPER(USERPRO, FECHAP);

