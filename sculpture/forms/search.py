import haystack.forms


class FacetedSearchForm (haystack.forms.FacetedSearchForm):

    """Form that has special handling of empty queries that have
    selected facets.

    The idea is that when no query is provided, the full facet counts
    are listed to enable browsing. Initially displaying all site
    reports on the map when there is no query makes page loading too
    slow, however, so there should be query results for no query only
    when there are selected facets.

    """

    def _get_sqs (self):
        if not self.is_valid():
            return self.no_query_found()
        elif not self.cleaned_data.get('q'):
            if self.selected_facets:
                sqs = self.searchqueryset.all()
            else:
                return self.no_query_found()
        else:
            sqs = self.searchqueryset.auto_query(self.cleaned_data['q'])
        if self.load_all:
            sqs = sqs.load_all()
        return sqs

    def search (self):
        sqs = self._get_sqs()
        for facet in self.selected_facets:
            if ":" not in facet:
                continue
            field, value = facet.split(":", 1)
            if value:
                sqs = sqs.narrow(u'%s:"%s"' % (field, sqs.query.clean(value)))
        return sqs
