from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from collections import OrderedDict as SortedDict
import haystack.views

import sculpture.utils


class FacetedSearchView (haystack.views.FacetedSearchView):

    def build_page (self):
        # Override Haystack's pagination logic so that invoking a
        # facet that reduces the number of pages of results below the
        # current page does not result in a 404.
        #
        # This is essentially the same code as Django 1.4's pagination
        # example.
        paginator = Paginator(self.results, self.results_per_page)
        page_number = self.request.GET.get('page')
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return (paginator, page)

    def create_response (self):
        # Set the search results on the session.
        if self.results:
            result_ids = [result.pk for result in self.results]
            self.request.session['search_results'] = result_ids
            self.request.session['search_page'] = self.request.get_full_path()
        self.selected_facets = self.form.selected_facets
        return super(FacetedSearchView, self).create_response()

    def extra_context (self):
        extra = super(FacetedSearchView, self).extra_context()
        extra.update(sculpture.utils.get_user_feedback_form(self.request))
        facets = self._remove_selected_facets(extra.get('facets'))
        if not self.query and not self.selected_facets:
            facets = self.searchqueryset.facet_counts()
        facets = self._link_facets(facets)
        facets = self._sort_facets(facets)
        facets = self._group_facets(facets)
        extra['facets'] = facets
        extra['base_url'] = self.request.path + '?' + \
            self.request.GET.urlencode()
        extra['selected_facets'] = self._link_selected_facets(
            self.selected_facets)
        return extra

    def _group_facets (self, facets):
        """Returns `facets` grouped appropriately.

        Currently this means creating a hierarchical grouping of
        FeatureSet values.

        """
        values = facets['fields']['feature_sets']
        group = SortedDict()
        for value, count, display, url in values:
            parts = value.split(': ')
            level = group
            for part in parts:
                # The part corresponds to the display name, so we
                # switch the two around here, and it gets switched
                # back in _group_facet_values. Why, you ask? Because
                # if we use the full value for the key
                # (level.setdefault), bad things happen to the
                # hierarchy.
                level = level.setdefault(part, SortedDict(
                        {'count': 0, 'display': '', 'url': None}))
                if part == parts[-1]:
                    level['count'] = count
                    level['url'] = url
                    level['display'] = value
        new_values = self._group_facet_values([], group)
        facets['fields']['feature_sets'] = new_values
        return facets

    def _group_facet_values (self, level, group):
        for key, value in group.items():
            if key in ('count', 'display', 'url'):
                continue
            new_level = []
            level.append([value['display'], value['count'], key, value['url'],
                          new_level])
            self._group_facet_values(new_level, value)
        return level

    def _link_facets (self, facets):
        """Returns `facets` annotated with a URL to the entity page
        for the object and a display name."""
        # It is not at all good that information about the specific
        # facets is held here. I'd go so far as to say this whole
        # method is absurd.
        models = {
            'country': sculpture.models.Country,
            'dedications_medieval': sculpture.models.Dedication,
            'dedications_now': sculpture.models.Dedication,
            'dioceses_medieval': sculpture.models.Diocese,
            'dioceses_now': sculpture.models.Diocese,
            'feature_sets': sculpture.models.FeatureSet,
            'glossary_terms': sculpture.models.GlossaryTerm,
            'regions_now': sculpture.models.Region,
            'regions_traditional': sculpture.models.Region,
            'settlement': sculpture.models.Settlement}
        for field, values in facets['fields'].items():
            try:
                model = models[field]
            except KeyError:
                continue
            # Sure, not all name fields are specified as unique in the
            # models.
            urls = {}
            for obj in model.objects.all():
                try:
                    urls[obj.name] = obj.get_absolute_url()
                except:
                    urls[obj.name] = None
            new_values = []
            for value in values:
                if field == 'feature_sets':
                    lookup_name = value[0].rsplit(': ')[-1]
                else:
                    lookup_name = value[0]
                try:
                    new_values.append((value[0], value[1], lookup_name,
                                       urls[lookup_name]))
                except KeyError:
                    pass
            facets['fields'][field] = new_values
        return facets

    def _link_selected_facets (self, selected_facets):
        """Returns `selected_facets` annotated with a URL for removing
        the facet."""
        facets = []
        query_params = self.request.GET.copy()
        for facet in selected_facets:
            field, value = self._split_facet(facet)
            query_string_facets = [
                other_facet for other_facet in selected_facets
                if other_facet != facet]
            query_params.setlist('selected_facets', query_string_facets)
            query_string = query_params.urlencode()
            remove_url = self.request.path
            if query_string:
                remove_url = remove_url + '?' + query_string
            name = '%s (%s)' % (value, field.replace('_', ' '))
            facets.append((name, remove_url))
        return facets

    def _sort_facets (self, facets):
        """Returns `facets` sorted alphabetically."""
        for field, values in facets['fields'].items():
            values.sort(key=lambda x: x[0].upper())
        return facets

    def _remove_selected_facets (self, facets):
        """Removes selected facets from the list of available
        facets."""
        if not facets:
            return None
        selected_facets = {}
        for facet in self.selected_facets:
            field, value = self._split_facet(facet)
            values = selected_facets.setdefault(field, [])
            values.append(value)
        for field, values in selected_facets.items():
            facets['fields'][field] = [item for item in facets['fields'][field]
                                       if item[0] not in values]
        return facets

    def _split_facet (self, facet):
        if ':' not in facet:
            return None, None
        field, value = facet.split(':', 1)
        if field.endswith('_exact'):
            field = field.rsplit('_', 1)[0]
        return field, value


class SiteFacetedSearchView (FacetedSearchView):

    def extra_context (self):
        extra = super(SiteFacetedSearchView, self).extra_context()
        extra.update(self._generate_site_marker_data())
        return extra

    def _generate_site_marker_data (self):
        data = []
        for result in self.results:
            latitude = result.latitude
            longitude = result.longitude
            if latitude is not None and longitude is not None:
                site = result.object
                data.append([[result.latitude, result.longitude],
                             site.get_title(), site.get_absolute_url()])
        return {'marker_data': data}
