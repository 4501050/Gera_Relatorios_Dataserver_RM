SELECT GIMAGEM.IMAGEM,
       CASE
         WHEN Substring(SPLETIVO.CODPERLET, 6, 1) LIKE '1' THEN '1º Sem./'
                                                                + Substring(SPLETIVO.CODPERLET, 1, 4)
         ELSE '2º Sem./'
              + Substring(SPLETIVO.CODPERLET, 1, 4)
       END                                                                                                                                            'PERIODO_LETIVO',
       SHABILITACAOFILIAL.CODTIPOCURSO,
       PPESSOA.NOME                                                                                                                                   AS ALUNO,
       Cast(SMATRICPL.IDPERLET AS VARCHAR)                                                                                                            PERIODOLETIVO,
       PERLET_CORRENTE.TEXTO                                                                                                                          PERLETCORRENTE,
       SMATRICPL.CODSTATUS,/*PPESSOA.CPF,*/ /*COEFICIENTE_RENDIMENTO.MEDIAGLOBAL*/
       SHABILITACAOALUNO.CR                                                                                                                           AS CR,
       CONCAT(Substring(PPESSOA.CPF, 1, 3), '.', Substring(PPESSOA.CPF, 4, 3), '.', Substring(PPESSOA.CPF, 7, 3), '-', Substring(PPESSOA.CPF, 10, 2)) AS CPF,
       CONVERT(VARCHAR(10), PPESSOA.DTNASCIMENTO, 103)                                                                                                AS DTNASCIMENTO,
       PPESSOA.NATURALIDADE,
       PCODNACAO.DESCRICAO                                                                                                                            NACIONALIDADE,
       PPESSOA.ESTADONATAL,
       SPLETIVO.OBS                                                                                                                                   AS 'PLetivoOBS',
       CASE
         WHEN SMATRICPL.CODSTATUS IN (19, 249, 34, 371, 48, 358, 104, 334, 78) THEN 1
         ELSE 0
       END                                                                                                                                            AS CODSTATUSVALD,
       CONCAT(PPESSOA.CARTIDENTIDADE, '/' + PPESSOA.ORGEMISSORIDENT + ' '
                                      + PPESSOA.UFCARTIDENT)                                                                                          AS RG,
       CASE
         WHEN GETD.NACIONAL = 'S' THEN 'Brasileira'
         ELSE GETD.NOME
       END                                                                                                                                            AS PAIS,
       SHABILITACAOALUNO.RA,
       Year(SHABILITACAOALUNO.DTCONCLUSAOCURSO)                                                                                                       AS ANO_CONCLUSAO,/*SAUTORIZACAOCURSO.PORTRECONHECIMENTO AS PORTARIA, CONVERT(VARCHAR(10),SAUTORIZACAOCURSO.DTRECONHECIMENTO,103) AS DT_PORTARIA, CONVERT(VARCHAR(10),SAUTORIZACAOCURSO.DTDOURECONHECIMENTO,103) AS DT_PUBLIC_PORTARIA,*/
       SHABILITACAOALUNO.IDHABILITACAOFILIAL,
       CONCAT(SCURSO.NOME, ' - ', SHABILITACAO.NOME)                                                                                                  AS CURSO,
       STURNO.NOME                                                                                                                                    AS TURNO,
       SESCOLA.NOME                                                                                                                                   AS FILIAL,
       CASE
         WHEN TIPOCAMPUS = 1 THEN 'CAMPUS ' + SCAMPUS.DESCRICAO
         WHEN TIPOCAMPUS = 2 THEN 'POLO ' + SCAMPUS.DESCRICAO
       END                                                                                                                                            CAMPUS,/*ISNULL(SCAMPUS.DESCRICAO, CASE WHEN SHABILITACAOFILIAL.CODFILIAL = 1 THEN 'HIGIENÓPOLIS' WHEN SHABILITACAOFILIAL.CODFILIAL = 2 THEN 'ALPHAVILLE' WHEN SHABILITACAOFILIAL.CODFILIAL = 7 THEN 'CAMPINAS' END)CAMPUS,*/
       STIPOCURSO.NOME                                                                                                                                AS NIVEL_ENSINO,
       CONVERT (VARCHAR (2), Day (Getdate())) + ' de '
       + CASE
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 1 THEN 'Janeiro'
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 2 THEN 'Fevereiro'
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 3 THEN 'Março'
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 4 THEN 'Abril'
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 5 THEN 'Maio'
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 6 THEN 'Junho'
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 7 THEN 'Julho'
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 8 THEN 'Agosto'
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 9 THEN 'Setembro'
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 10 THEN 'Outubro'
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 11 THEN 'Novembro'
           WHEN CONVERT (VARCHAR (2), Month (Getdate())) = 12 THEN 'Dezembro'
         END
       + ' de '
       + CONVERT (VARCHAR (4), Year (Getdate())) + '.'                                                                                                AS DT_HOJE,
       GFILIAL.CIDADE                                                                                                                                 AS FILIAL_CIDADE,
       SGRADE.CARGAHORARIA                                                                                                                            AS CH,
       CASE
         WHEN SPLETIVO.CODTIPOCURSO <> 4 THEN (SELECT CASE
                                                        WHEN SAUTORIZACAOCURSO.DTRECONHECIMENTO IS NOT NULL THEN ISNULL(PORTRECONHECIMENTO, '') + ' de '
                                                                                                                 + ISNULL(Cast(FORMAT(SAUTORIZACAOCURSO.DTRECONHECIMENTO, 'dd/MM/yyyy') AS VARCHAR(15)), '')
                                                                                                                 + ', ' + ' publicada em '
                                                                                                                 + ISNULL(Cast(FORMAT(DTDOURECONHECIMENTO, 'dd/MM/yyyy') AS VARCHAR(15)), '')
                                                        WHEN SAUTORIZACAOCURSO.DTAUTORIZACAO IS NOT NULL THEN ISNULL(PORTAUTORIZACAO, '') + ' de '
                                                                                                              + ISNULL(Cast(FORMAT(SAUTORIZACAOCURSO.DTAUTORIZACAO, 'dd/MM/yyyy') AS VARCHAR(15)), '')
                                                                                                              + ' publicada em '
                                                                                                              + ISNULL(Cast(FORMAT(DTDOUAUTORIZACAO, 'dd/MM/yyyy') AS VARCHAR(15)), '')
                                                        WHEN SAUTORIZACAOCURSO.DTRESOLUCAO IS NOT NULL THEN ISNULL(NUMRESOLUCAO, '') + ' de '
                                                                                                            + ISNULL(Cast(FORMAT(SAUTORIZACAOCURSO.DTRESOLUCAO, 'dd/MM/yyyy') AS VARCHAR(15)), '')
                                                                                                            + ' publicada em '
                                                                                                            + ISNULL(Cast(FORMAT(DTDOUAUTORIZACAO, 'dd/MM/yyyy') AS VARCHAR(15)), '')
                                                      END
                                               FROM   SAUTORIZACAOCURSO
                                               WHERE  SAUTORIZACAOCURSO.CODCOLIGADA = 1
                                                      AND SAUTORIZACAOCURSO.IDHABILITACAOFILIAL = SHABILITACAOFILIAL.IDHABILITACAOFILIAL
                                                      AND SAUTORIZACAOCURSO.CODAUTORIZACURSO = CODAUTORIZACAO.CODAUTORIZACURSO)
         ELSE 'Reconhecido pela Portaria MEC nº 609 de 14/03/2019 Publicado no Diário Oficial da União em 18/03/2019'
       END                                                                                                                                            PORTARIA,
       SHABILITACAOFILIAL.DECRETOCURSO                                                                                                                AS PORTARIA2,
       SPLETIVO.OBS                                                                                                                                   AS 'PLetivoOBS',
       SESCOLA.NOME                                                                                                                                   'UNIDADEACAD' /*GMUD 437610 S250117-0082*/
       /*FLAN.STATUSLAN8*/
FROM   SHABILITACAOALUNO (NOLOCK)
       INNER JOIN SALUNO (NOLOCK)
               ON SALUNO.CODCOLIGADA = SHABILITACAOALUNO.CODCOLIGADA
                  AND SALUNO.RA = SHABILITACAOALUNO.RA
       INNER JOIN PPESSOA (NOLOCK)
               ON PPESSOA.CODIGO = SALUNO.CODPESSOA
       INNER JOIN SHABILITACAOFILIAL (NOLOCK)
               ON SHABILITACAOALUNO.CODCOLIGADA = SHABILITACAOFILIAL.CODCOLIGADA
                  AND SHABILITACAOALUNO.IDHABILITACAOFILIAL = SHABILITACAOFILIAL.IDHABILITACAOFILIAL
       INNER JOIN SHABILITACAO (NOLOCK)
               ON SHABILITACAOFILIAL.CODCOLIGADA = SHABILITACAO.CODCOLIGADA
                  AND SHABILITACAOFILIAL.CODHABILITACAO = SHABILITACAO.CODHABILITACAO
                  AND SHABILITACAOFILIAL.CODCURSO = SHABILITACAO.CODCURSO
       INNER JOIN SMATRICPL (NOLOCK)
               ON SMATRICPL.CODCOLIGADA = SHABILITACAOALUNO.CODCOLIGADA
                  AND SMATRICPL.IDHABILITACAOFILIAL = SHABILITACAOALUNO.IDHABILITACAOFILIAL
                  AND SMATRICPL.RA = SHABILITACAOALUNO.RA
       INNER JOIN SPLETIVO (NOLOCK)
               ON SMATRICPL.CODCOLIGADA = SPLETIVO.CODCOLIGADA
                  AND SMATRICPL.IDPERLET = SPLETIVO.IDPERLET
       INNER JOIN STIPOCURSO (NOLOCK)
               ON STIPOCURSO.CODCOLIGADA = SHABILITACAOFILIAL.CODCOLIGADA
                  AND STIPOCURSO.CODTIPOCURSO = SHABILITACAOFILIAL.CODTIPOCURSO
       INNER JOIN SCURSO (NOLOCK)
               ON SHABILITACAOFILIAL.CODCOLIGADA = SCURSO.CODCOLIGADA
                  AND SHABILITACAOFILIAL.CODCURSO = SCURSO.CODCURSO
       INNER JOIN SESCOLA (NOLOCK)
               ON SCURSO.CODCOLIGADA = SESCOLA.CODCOLIGADA
                  AND SCURSO.CODESCOLA = SESCOLA.CODESCOLA
       INNER JOIN SGRADE (NOLOCK)
               ON SGRADE.CODCOLIGADA = SHABILITACAOFILIAL.CODCOLIGADA
                  AND SGRADE.CODCURSO = SHABILITACAOFILIAL.CODCURSO
                  AND SGRADE.CODHABILITACAO = SHABILITACAOFILIAL.CODHABILITACAO
                  AND SGRADE.CODGRADE = SHABILITACAOFILIAL.CODGRADE
       INNER JOIN STURNO (NOLOCK)
               ON STURNO.CODCOLIGADA = SHABILITACAOFILIAL.CODCOLIGADA
                  AND STURNO.CODTURNO = SHABILITACAOFILIAL.CODTURNO
       LEFT JOIN GMUNICIPIO (NOLOCK)
              ON GMUNICIPIO.CODETDMUNICIPIO = PPESSOA.ESTADONATAL
                 AND GMUNICIPIO.NOMEMUNICIPIO = PPESSOA.NATURALIDADE
       LEFT JOIN GETD (NOLOCK)
              ON GETD.CODETD = GMUNICIPIO.CODETDMUNICIPIO
       LEFT JOIN PCODNACAO (NOLOCK)
              ON PPESSOA.NACIONALIDADE = PCODNACAO.CODCLIENTE
       INNER JOIN GFILIAL (NOLOCK)
               ON GFILIAL.CODCOLIGADA = SHABILITACAOFILIAL.CODCOLIGADA
                  AND GFILIAL.CODFILIAL = SHABILITACAOFILIAL.CODFILIAL
       LEFT JOIN GIMAGEM (NOLOCK)
              ON GIMAGEM.ID = GFILIAL.IDIMAGEM
       LEFT JOIN SCAMPUS (NOLOCK)
              ON SCAMPUS.CODCAMPUS = SHABILITACAOALUNO.CODCAMPUS
       LEFT JOIN (SELECT Sum (CASE
                                WHEN SHISTDISCCONCLUIDAS.STATUS = '*Equiv.' THEN SHISTDISCEQUIVCONCLUIDAS.NOTA
                                ELSE SHISTDISCCONCLUIDAS.NOTA
                              END) / Count (SHISTDISCCONCLUIDAS.RA) AS MEDIAGLOBAL,
                         SHISTDISCCONCLUIDAS.RA,
                         SHISTDISCCONCLUIDAS.IDHABILITACAOFILIAL,
                         SHISTDISCCONCLUIDAS.CODCOLIGADA
                  FROM   SHISTDISCCONCLUIDAS (NOLOCK)
                         LEFT JOIN SHISTDISCEQUIVCONCLUIDAS (NOLOCK)
                                ON SHISTDISCEQUIVCONCLUIDAS.CODCOLIGADA = SHISTDISCCONCLUIDAS.CODCOLIGADA
                                   AND SHISTDISCEQUIVCONCLUIDAS.RA = SHISTDISCCONCLUIDAS.RA
                                   AND SHISTDISCEQUIVCONCLUIDAS.IDHABILITACAOFILIAL = SHISTDISCCONCLUIDAS.IDHABILITACAOFILIAL
                                   AND SHISTDISCEQUIVCONCLUIDAS.GREQUIV = SHISTDISCCONCLUIDAS.GREQUIV
                  WHERE  SHISTDISCCONCLUIDAS.CODCOLIGADA = :$CODCOLIGADA
                         AND SHISTDISCCONCLUIDAS.RA = :P_RA
                         AND SHISTDISCCONCLUIDAS.IDHABILITACAOFILIAL = :P_IDHABILITACAOFILIAL /*As Disciplinas de Atividades Complementares, não geram notas (ficam com notas 0.0), e ela estava entrando na regra, e fazendo a Média Global do aluno abaixar.*/
                         AND CASE
                               WHEN SHISTDISCCONCLUIDAS.STATUS = '*Equiv.' THEN SHISTDISCEQUIVCONCLUIDAS.NOTA
                               ELSE SHISTDISCCONCLUIDAS.NOTA
                             END > 0.0
                  GROUP  BY SHISTDISCCONCLUIDAS.RA,
                            SHISTDISCCONCLUIDAS.IDHABILITACAOFILIAL,
                            SHISTDISCCONCLUIDAS.CODCOLIGADA) COEFICIENTE_RENDIMENTO
              ON COEFICIENTE_RENDIMENTO.CODCOLIGADA = SMATRICPL.CODCOLIGADA
                 AND COEFICIENTE_RENDIMENTO.RA = SMATRICPL.RA
                 AND COEFICIENTE_RENDIMENTO.IDHABILITACAOFILIAL = SMATRICPL.IDHABILITACAOFILIAL
       OUTER APPLY (SELECT TOP 1 ( CODAUTORIZACURSO ) CODAUTORIZACURSO
                    FROM   SAUTORIZACAOCURSO (NOLOCK)
                    WHERE  SAUTORIZACAOCURSO.CODCOLIGADA = SHABILITACAOFILIAL.CODCOLIGADA
                           AND SAUTORIZACAOCURSO.IDHABILITACAOFILIAL = SHABILITACAOFILIAL.IDHABILITACAOFILIAL
                           AND SAUTORIZACAOCURSO.ULTIMAAUTORIZACAOVALIDA = 'S' /*AND SAUTORIZACAOCURSO.ULTIMAAUTORIZACAOVALIDA = 'S'*/)CODAUTORIZACAO
       OUTER APPLY (SELECT TEXTO
                    FROM   SPARAM (NOLOCK)
                           INNER JOIN SPLETIVO SP (NOLOCK)
                                   ON SPARAM.CODCOLIGADA = SP.CODCOLIGADA
                                      AND SPARAM.ID = 'IDPERLET'
                                      AND SPARAM.TEXTO = SP.IDPERLET
                                      AND SP.CODCOLIGADA = :$CODCOLIGADA
                                      AND SP.CODFILIAL = :$CODFILIAL
                                      AND SP.CODTIPOCURSO = :$CODTIPOCURSO )PERLET_CORRENTE /*GMUD 437610 S250117-0082 INICIO*/
       /*LEFT JOIN SCONTRATO WITH (NOLOCK)
               ON SCONTRATO.CODCOLIGADA = SMATRICPL.CODCOLIGADA
                  AND SCONTRATO.IDHABILITACAOFILIAL = SMATRICPL.IDHABILITACAOFILIAL
                  AND SCONTRATO.RA = SMATRICPL.RA
                  AND SCONTRATO.IDPERLET = SMATRICPL.IDPERLET
                  AND SCONTRATO.STATUS = 'N'
                  AND SCONTRATO.TIPOCONTRATO = 'P'
                  
                  
       LEFT JOIN SPARCELA WITH (NOLOCK)
               ON SPARCELA.CODCOLIGADA = SCONTRATO.CODCOLIGADA
                  AND SPARCELA.RA = SCONTRATO.RA
                  AND SPARCELA.IDPERLET = SCONTRATO.IDPERLET
                  AND SPARCELA.CODCONTRATO = SCONTRATO.CODCONTRATO
                  AND SPARCELA.PARCELA = 1 /* movido do WHERE para preservar o LEFT JOIN */
       LEFT JOIN SLAN WITH (NOLOCK)
              ON SLAN.CODCOLIGADA = SPARCELA.CODCOLIGADA
                 AND SLAN.IDPARCELA = SPARCELA.IDPARCELA
       LEFT JOIN FLAN WITH (NOLOCK)
              ON FLAN.CODCOLIGADA = SLAN.CODCOLIGADA
                 AND FLAN.IDLAN = SLAN.IDLAN /*GMUD 437610 S250117-0082 TERMINO*/*/
WHERE  /* SHABILITACAOFILIAL.CODFILIAL = 1 AND SHABILITACAOFILIAL.CODTIPOCURSO = 2*/
  SMATRICPL.CODCOLIGADA = :$CODCOLIGADA
  AND SMATRICPL.RA = :P_RA
  AND SMATRICPL.IDHABILITACAOFILIAL = :P_IDHABILITACAOFILIAL
  AND SMATRICPL.IDPERLET = :P_IDPERLET
  AND SPLETIVO.CODTIPOCURSO = :$CODTIPOCURSO
  AND SPLETIVO.CODFILIAL = :$CODFILIAL /*GMUD 437610 S250117-0082*/
    /*AND SPARCELA.PARCELA = 1*/ 
