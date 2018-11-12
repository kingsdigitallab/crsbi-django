<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet extension-element-prefixes="str"
                xmlns:str="http://exslt.org/strings"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:template match="/">
    <site>
      <xsl:apply-templates select="/TEI.2/teiHeader/fileDesc/titleStmt/author" />
      <xsl:apply-templates select="/TEI.2/text/*/div" />
    </site>
  </xsl:template>

  <xsl:template match="author">
    <!-- Instead of having multiple author elements, multiple author
         names are in a single element, separated by ", ", or "; ", or
         " and ", or.... Deal with the least pathological cases. -->
    <xsl:choose>
      <xsl:when test=". = 'John and Sarah Blair'">
        <xsl:call-template name="make-author">
          <xsl:with-param name="name" select="'John Blair'" />
        </xsl:call-template>
        <xsl:call-template name="make-author">
          <xsl:with-param name="name" select="'Sarah Blair'" />
        </xsl:call-template>
      </xsl:when>
      <xsl:when test="contains(., ' and ')">
        <xsl:call-template name="make-author">
          <xsl:with-param name="name" select="substring-before(., ' and ')" />
        </xsl:call-template>
        <xsl:call-template name="make-author">
          <xsl:with-param name="name" select="substring-after(., ' and ')" />
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:for-each select="str:tokenize(., ',;/')">
          <xsl:call-template name="make-author">
            <xsl:with-param name="name" select="." />
          </xsl:call-template>
        </xsl:for-each>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="div[@type='biblio']">
    <bibliography>
      <xsl:apply-templates select="listBibl/bibl" />
    </bibliography>
  </xsl:template>

  <xsl:template match="div[@type='comments']">
    <comments>
      <xsl:apply-templates select="*" mode="text" />
    </comments>
  </xsl:template>

  <xsl:template match="div[@type='featureset']">
    <features>
      <xsl:apply-templates select=".//div[@type='feature']" mode="feature" />
    </features>
  </xsl:template>

  <xsl:template match="div[@type='gendesc']">
    <description>
      <xsl:apply-templates select="*" mode="text" />
    </description>
    <xsl:apply-templates select="table[@type='pictures']" />
  </xsl:template>

  <xsl:template match="div[@type='history']">
    <history>
      <xsl:apply-templates select="*" mode="text" />
    </history>
  </xsl:template>

  <xsl:template match="div[@type='location']">
    <location>
      <xsl:apply-templates select="ab/placeName/name[not(@type)]" />
      <xsl:apply-templates select="ab/placeName/country" />
      <regions>
        <xsl:apply-templates select="ab/placeName/region" />
      </regions>
      <dioceses>
        <xsl:apply-templates select="ab/placeName/orgName[@type='diocese']" />
      </dioceses>
      <dedications>
        <xsl:apply-templates select="ab/placeName/name[@type='dedication']" />
      </dedications>
      <xsl:apply-templates select="ab/placeName/settlement" />
      <grid_reference>
        <xsl:value-of select="ab/placeName/@key" />
      </grid_reference>
    </location>
  </xsl:template>

  <xsl:template match="listBibl/bibl/title|listBibl/bibl/hi">
    <i>
      <xsl:apply-templates />
    </i>
  </xsl:template>

  <xsl:template match="name">
    <xsl:copy>
      <xsl:value-of select="." />
    </xsl:copy>
  </xsl:template>

  <xsl:template match="name[@type='dedication']">
    <dedication>
      <xsl:apply-templates />
    </dedication>
  </xsl:template>

  <xsl:template match="orgName[@type='diocese']">
    <diocese>
      <xsl:apply-templates />
    </diocese>
  </xsl:template>

  <xsl:template match="region">
    <xsl:for-each select="name">
      <region>
        <xsl:copy-of select="../@*" />
        <xsl:copy-of select="../date" />
        <name>
          <xsl:apply-templates select="node()[name() != 'date']" />
        </name>
        <xsl:if test="date">
          <subdate>
            <xsl:apply-templates select="date/node()" />
          </subdate>
        </xsl:if>
      </region>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="settlement">
    <settlement>
      <xsl:value-of select="@type" />
    </settlement>
  </xsl:template>

  <xsl:template match="table[@type='pictures']">
    <images>
      <xsl:apply-templates select="row/cell[figure]" mode="image" />
    </images>
  </xsl:template>

  <xsl:template match="TEI.2|teiHeader|text|front">
    <xsl:apply-templates />
  </xsl:template>

  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>

  <!-- mode: feature -->

  <xsl:template match="div[@type='feature']" mode="feature">
    <feature>
      <name>
        <xsl:apply-templates select="head" mode="feature" />
      </name>
      <xsl:apply-templates select="../head" mode="feature_set" />
      <xsl:apply-templates select=".//table[@type='pictures']" />
      <!-- Sometimes (as in id-ma-balli.xml) the figures are
           associated with a feature set rather than the feature. -->
      <xsl:if test="not(preceding-sibling::div[@type='feature']) and
                    not(following-sibling::div[@type='feature'])">
        <xsl:apply-templates
            select="preceding-sibling::table[@type='pictures']" />
      </xsl:if>
      <details>
        <xsl:apply-templates select="div[@type='detail']"
                             mode="feature" />
      </details>
      <xsl:apply-templates select="div[head/@type='dimensions']"
                           mode="feature" />
      <description>
        <xsl:apply-templates select="*" mode="text" />
      </description>
    </feature>
  </xsl:template>

  <xsl:template match="div[@type='detail']" mode="feature">
    <detail>
      <name>
        <xsl:value-of select="head" />
      </name>
      <description>
        <xsl:apply-templates select="*" mode="text" />
      </description>
    </detail>
  </xsl:template>

  <xsl:template match="div[head/@type='dimensions']" mode="feature">
    <dimensions>
      <xsl:apply-templates select="table/row" mode="feature" />
    </dimensions>
  </xsl:template>

  <xsl:template match="row" mode="feature">
    <dimension>
      <type>
        <xsl:value-of select="cell[@role='type']" />
      </type>
      <value>
        <xsl:value-of select="cell[@role='value']" />
      </value>
      <section>
        <xsl:value-of select="preceding-sibling::head" />
      </section>
    </dimension>
  </xsl:template>

  <!-- mode: feature_set -->

  <xsl:template match="head" mode="feature_set">
    <feature_set>
      <name>
        <xsl:value-of select="." />
      </name>
      <xsl:apply-templates select="ancestor::div[@type='featureset'][2]/head"
                           mode="feature_set" />
    </feature_set>
  </xsl:template>

  <!-- mode: image -->

  <xsl:template match="cell" mode="image">
    <image url="{ figure/@url }">
      <xsl:value-of select="caption" />
    </image>
  </xsl:template>

  <!-- mode: text -->

  <xsl:template match="*" mode="text">
    <xsl:apply-templates mode="text" />
  </xsl:template>

  <xsl:template match="div[@type='detail']" mode="text" />

  <xsl:template match="head" mode="text" />

  <xsl:template match="p" mode="text">
    <xsl:copy>
      <xsl:apply-templates mode="text" />
    </xsl:copy>
  </xsl:template>

  <xsl:template match="table[@type='dimensions']" mode="text" />
  <xsl:template match="table[@type='sub-dimensions']" mode="text" />

  <xsl:template match="table[@type='pictures']" mode="text" />

  <!-- Named templates. -->

  <xsl:template name="make-author">
    <xsl:param name="name" />
    <author>
      <xsl:value-of select="normalize-space($name)" />
    </author>
  </xsl:template>

</xsl:stylesheet>
