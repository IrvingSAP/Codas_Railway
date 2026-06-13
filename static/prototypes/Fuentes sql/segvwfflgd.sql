--------------------------------------------------------------------
-- NOMBRE DE SCRIPT....: SEGVWFFLGDTA                             --
-- DESCRIPCIÓN.........: VISTA PARA MOSTRAR EL REGISTRO MAS ACTUAL--
--                       DE LAS ULTIMAS 24 HORAS POR USUARIO      --
-- TIPO OBJETO.........: VIEW                                     --
-- REQUERIMIENTO.......: SEG - GESTION DESBLOQUEO DE USUARIOS     --
-- SUBDOMINIO..........: MODERNIZACIÓN DE LA TECNOLOGÍA.          --
-- FECHA DE CREACIÓN...: MAYO DE 2020                             --
-- AUTOR...............: ANDRES RIVERA CARVAJAL - PERSONAL SOFT   --
-- BASE DE DATOS RELACIONAL:  DB2 FOR I                           --
--------------------------------------------------------------------
-- MODIFICACIONES:                                                --
-- FECHA DE MODIFICACIÓN :                                        --
-- AUTOR...............  :                                        --
-- DESCRIPCIÓN ......... :                                        --
-- REQUERIMIENTO.........:                                        --
--------------------------------------------------------------------

 --CREATE OR REPLACE VIEW &LIB/SEGVWFFLGD (
 CREATE OR REPLACE VIEW &LIB/SEGVWFFLGD (
   USUARIO, FECHMODIF, HORAMODIF, ESTADO, CORREO_USU, DETALL_ACC)
 AS
 SELECT
   USUARIO, FECHMODIF, HORAMODIF, ESTADO, CORREO_USU, DETALL_ACC
	FROM &LIB/SEGFFLGDBD A
 INNER JOIN
	  (SELECT USUARIO AS USR, MAX(HORAMODIF) AS MAXH
		  FROM &LIB/SEGFFLGDBD
	   WHERE (VARCHAR_FORMAT(CURRENT DATE, 'YYYYMMDD') - FECHMODIF)
           <= 1 GROUP BY USUARIO)
 ON (A.USUARIO = USR AND A.HORAMODIF = MAXH)
 RCDFMT RSEGVWFFLG;
