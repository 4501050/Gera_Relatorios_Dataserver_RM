SELECT contx.CODFILIAL,
       mec.RUA,
       mec.NUMERO,
       mec.COMPLEMENTO,
       mec.BAIRRO,
       mec.CODMUNICIPIO,
       mec.ESTADO,
       mec.CEP,
       mec.EMAIL,
       mec.DDD,
       mec.TELEFONE,
       mec.CODINEPINSTITUICAO,
       mec.CODEMEC,
       
       dir.CODPESSOA,
       p1.NOME AS NOME_DIRETOR,
       img_dir.IMAGEM AS ASSINATURA_DIRETOR, 
       dir.CODPESSOASEC1,
       p2.NOME AS NOME_SECRETARIO,
       img_sec.IMAGEM AS ASSINATURA_SECRETARIO, 
       dir.AUTORIZDIR,
       dir.AUTORIZSEC1,
       mec.IDINSTITUICAOMEC,
       CASE 
            WHEN contx.CODFILIAL = 20 AND dir.IDINSTITUICAOMEC = 13 
                THEN 'www.mackenzie.br/fempar'
            ELSE 'www.mackenzie.br/'    
       END AS URL_SITE,

       /* Campos autorização da instituição */
CASE aut.ATOREGULATORIO
     WHEN 1 THEN 'Credenciamento'
            WHEN 2 THEN 'Recredenciamento'
            WHEN 3 THEN 'Renovação de credenciamento'
    ELSE ''
END AS TIPOAUTORIZ,
       
       CASE aut.TIPOAUTORIZ
             WHEN 0 THEN 'pelo Decreto'
    WHEN 1 THEN 'pela Portaria'
    WHEN 2 THEN 'pela Resolução'
    WHEN 3 THEN 'pela Ata'
    WHEN 4 THEN 'pelo Parecer'
    WHEN 5 THEN 'pela Lei federal'
    WHEN 6 THEN 'pela Lei estadual'
    WHEN 7 THEN 'pela Lei municipal'
    WHEN 8 THEN 'pelo Ato próprio'
            ELSE ''
       END AS ATOREGULATORIO,
       
       
       CONVERT(VARCHAR, aut.DTAUTORIZ, 103) AS DTAUTORIZ,
			aut.NRAUTORIZ,
       aut.LOCALAUTORIZ,
       aut.ULTIMAAUTORIZACAOVALIDA,
       aut.CODINSTITUICAO,
       aut.NUMEROPROCESSO,
       aut.TIPOPROCESSO,
       aut.PAGINAPUBLICACAO,
       aut.SECAOPUBLICACAO,
       aut.NUMPUBLICACAO,

       CONVERT(VARCHAR, aut.DATAPROTOCOLO, 103) AS DATAPROTOCOLO,
       CONVERT(VARCHAR, aut.DATACADASTRO, 103) AS DATACADASTRO,
	   CONVERT(VARCHAR, aut.DTPUBLICACAO, 103) AS DTPUBLICACAO,
       
       aut.MODALIDADECREDENCIAMENTO
FROM   SINSTITUICAOMEC mec (NOLOCK)
       INNER JOIN SCONTEXTOSINSTITUICAOMEC contx (NOLOCK)
               ON mec.CODCOLIGADA = contx.CODCOLIGADAINSTMEC
               AND mec.IDINSTITUICAOMEC = contx.IDINSTITUICAOMEC
       LEFT JOIN SDIRECAOFILIAL dir (NOLOCK)
               ON mec.CODCOLIGADA = dir.CODCOLIGADA
               AND mec.IDINSTITUICAOMEC = dir.IDINSTITUICAOMEC 
               
       LEFT JOIN PPESSOA p1 (NOLOCK)
               ON p1.CODIGO = dir.CODPESSOA
       LEFT JOIN PPESSOA p2 (NOLOCK)
               ON p2.CODIGO = dir.CODPESSOASEC1
       LEFT JOIN GIMAGEM img_dir (NOLOCK) 
               ON img_dir.ID = dir.IDASSINATURA
       LEFT JOIN GIMAGEM img_sec (NOLOCK) 
               ON img_sec.ID = dir.IDASSINATURASEC1 

       /* Relacionamento corrigido: Vinculo por Instituição + Filtro Ativa */
       LEFT JOIN SAUTORIZACAOFILIAL aut (NOLOCK)
               ON mec.CODCOLIGADA = aut.CODCOLIGADA
               AND mec.IDINSTITUICAOMEC = aut.IDINSTITUICAOMEC
               AND aut.ULTIMAAUTORIZACAOVALIDA = 'S'
  
WHERE  contx.CODFILIAL = :$CODFILIAL
   AND contx.CODTIPOCURSO = :$CODTIPOCURSO


/*
WHERE  contx.CODFILIAL = 1
   AND contx.CODTIPOCURSO = 3

*/