<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet exclude-result-prefixes="pndsdc xsl"
                xmlns:dc="http://purl.org/dc/elements/1.1/"
                xmlns:dcterms="http://purl.org/dc/terms/"
                xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                xmlns:pndsdc="http://purl.org/mla/pnds/pndsdc/"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="2.0">

  <xsl:output method="xml" indent="yes" encoding="UTF-8" />

  <xsl:strip-space elements="*" />

  <xsl:template match="pndsdc:description">
    <oai_dc:dc xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
      <xsl:apply-templates />
    </oai_dc:dc>
  </xsl:template>

  <xsl:template match="dcterms:license">
    <dc:rights>
      <xsl:value-of select="@valueURI" />
    </dc:rights>
  </xsl:template>

  <xsl:template match="dcterms:rightsHolder" />

  <xsl:template match="dcterms:spatial">
    <dc:coverage>
      <xsl:apply-templates />
    </dc:coverage>
  </xsl:template>

  <xsl:template match="dcterms:temporal">
    <dc:coverage>
      <xsl:apply-templates />
    </dc:coverage>
  </xsl:template>

  <xsl:template match="@encSchemeURI" />

  <xsl:template match="@valueURI" />

  <xsl:template match="@* | node()">
    <xsl:copy>
      <xsl:apply-templates select="@* | node()" />
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
