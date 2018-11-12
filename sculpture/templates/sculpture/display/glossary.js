{% for term in terms %}
$('a.glossary.{{ term.id }}').qtip({content: {text: '{{ term.description|escapejs }}' } });
{% endfor %}