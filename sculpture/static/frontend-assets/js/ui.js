/**
 * CRSBI User Interface Javascript.
 * Requires jquery/foundation 4.
 *
 * Questions? Brian.maher@kcl.ac.uk 
 */

var image = 1;

var switcher;



function browseSwitchToGrid()
{
	$(".result-icon").css({"display":"inline-block"});
	$(".result-list").hide();
}

function browseSwitchToList()
{
	$(".result-icon").hide();
	$(".result-list").show();
}

function cookie_set(c_name,value,exdays)
{
	var exdate=new Date();
	exdate.setDate(exdate.getDate() + exdays);
	var c_value=escape(value) + ((exdays==null) ? "" : "; expires="+exdate.toUTCString());
	document.cookie=c_name + "=" + c_value;
}

function cookie_get(c_name)
{
	var c_value = document.cookie;
	var c_start = c_value.indexOf(" " + c_name + "=");
	if (c_start == -1)
	{
		c_start = c_value.indexOf(c_name + "=");
	}
	if (c_start == -1)
	{
		c_value = null;
	}
	else
	{
		c_start = c_value.indexOf("=", c_start) + 1;
		var c_end = c_value.indexOf(";", c_start);
		if (c_end == -1)
		{
			c_end = c_value.length;
		}
		c_value = unescape(c_value.substring(c_start,c_end));
	}
	return c_value;
}


// Browsing by map
function initBrowseMap()
{
	
	if($('.browse-map').length && !$('.browse-map').hasClass("results-map"))
	{
	
	
		var geoJsonHighlight = {
		//  color: 'red',
		  weight:3,
		  opacity:0.8
		};

		var geoJsonInvisible = {
		    opacity: 0,
		  fillOpacity:0
		};

		var geoJsonSelected = {
		    opacity: 0.5,
		    fillOpacity:0.2
		};
	
		var label = new L.Label();
		
		var maptype="traditional"; // Default type = traditional
		var overlay_layer, irish_layer; // Declare these in scope
		
		
		
		function addLayersToMap()
		{
			var counties_to_use;
			
			if(maptype == "now")
			{
				counties_to_use = counties_now;
			} else
			{
				counties_to_use = counties_traditional;
			}
			
			overlay_layer = L.geoJson(counties_to_use, {
			    style:geoJsonInvisible,
	            onEachFeature: function(feature,layer){
	            	if(typeof feature.properties != 'undefined')
	            	{

						var name = feature.properties.NAME;
					
		                layer.on('mouseover',function(){
		                  layer.setStyle(geoJsonHighlight);
		
					  
		                });
		                layer.on('mouseout', function(){
		                  layer.setStyle(geoJsonInvisible);
		                });
						var count = $('div[data-field="regions_' + maptype + '_exact"]').find('a[for="' + name + '"]').parent().find(".facet-count").text();
						if(count == "") count = "0";
						layer.bindLabel(name + " (" + count + ")");
						layer.on('click', function()
						{
							var href=$('div[data-field="regions_' + maptype + '_exact"]').find('a[for="' + name + '"]').attr("href");
							if(href != undefined)
							{
								window.location.href = $('div[data-field="regions_' + maptype + '_exact"]').find('a[for="' + name + '"]').attr("href");
							}
						});

					}
				},
			});
			
	
		

			overlay_layer.addTo(map);
			
			
		}


		addLayersToMap();
		
		// This enables the map switcher between traditional and now.
		
		$("body").on("click", ".boundary_switcher a", function(event)
		{
			event.preventDefault();
			
			$(".boundary_switcher a").removeClass("current");
			$(this).addClass("current");
			
			// set maptype variable
			maptype = $(this).attr("data-type");
			
			// Clear layers
			overlay_layer.clearLayers();
			
			// Reset layers
			addLayersToMap();
		});
		
		
	    /*
	              
	                   layer.on('click',function(){
	   				  // Lose other drawn objects...
	                     for (lyr in drawnItems._layers) {
	                       drawnItems.removeLayer(drawnItems._layers[lyr]);
	                     };
	                     $('#id_geojson').val("");
	                     updateFacets(feature.properties.FIPS);                  
                
		*/
		
	}
}

// Enables the dynamic search box
function initDynamicSearch()
{
	$("body").on("click", "li.dynamic-search a[href='#search']", function(event)
	{
		event.preventDefault();
		$(".dynamic-search-holder").toggle("fast");
	});
	
	$("body").on("click", ".dynamic-search-go", function(event)
	{
		if($(".dynamic-search-box").val() == "")
		{
			alert("Please enter a search term.");
		} else
		{
			if($("input[name='search-selection']:checked").val() == "dynamic-site")
			{
				window.location.href="/browse/?q=" + $(".dynamic-search-box").val();
			} else
			{
				window.location.href="/browse/image/?q=" + $(".dynamic-search-box").val();
			}
		}
	});
	
	$("body").on("keyup", ".dynamic-search-box", function(event)
	{
		if(event.keyCode == 13)
		{
			$('.dynamic-search-go').click();
		}
	});
	
}

// Enables image fadign on homepage
function initHomeHeader()
{
	if($(".site-header.home").length)
	{
		
		switcher = window.setInterval(rotateHomepage, 7500);
		
		
		$("body").on("click", ".site-header .switcher i", function(event)
		{
			event.preventDefault();
			clearInterval(switcher);
			image = $(this).index();
			rotateHomepage();
			switcher = window.setInterval(rotateHomepage, 7500);
			
		});
	}
}

// Enables the site page image browsers
function initImageBrowser()
{
	
	$("body").on("click", ".browser_keys a", function(event)
	{
		event.preventDefault();
		
		var url = $(this).find("img").attr("src");
		var hreftemp = $(this).attr("href");
		var captiontemp = $(this).closest('.restrictor').siblings('.image-caption').text();

		$(this).find("img").attr("src", $(this).closest(".image_browser").find(".browser_primary img").attr("src"));
		$(this).attr("href", $(this).closest(".image_browser").find(".browser_primary a").attr("href"));
		$(this).closest('.restrictor').siblings('.image-caption').text($('.browser_primary .image-caption').text());
		
		$(this).closest(".image_browser").find(".browser_primary a img").attr("src", url);
		$(this).closest(".image_browser").find(".browser_primary a ").attr("href", hreftemp);
		$(this).closest(".image_browser").find(".browser_primary .image-caption ").text(captiontemp);
		
	});
	
	// Inline feature set browser
	$("body").on("click", ".inline_image_browser a:not(.feature-link)", function(event)
	{
		event.preventDefault();
		
		$(this).parent().parent().find(".primary").html($(this).html() + "<a class='feature-link' href='" + $(this).attr("href") + "' style='float: right; margin-top: 10px;'>View Details &raquo;</a>");
		
		if(!$(this).parent().parent().find(".primary").is(":visible"))
		{
			$(this).parent().parent().find(".primary").slideDown().scrollTop();
		}
		
	});
}

// Enables faceting
function initFaceting()
{
	// Enables showing/hiding of facets
	$('body').on("click", ".facet-title", function(event)
	{
		event.preventDefault();
		
		if($(this).closest(".facet").children(".facet-options").is(":visible"))
		{
			$(this).closest(".facet").children(".facet-options").slideUp();
			$(this).find("i").removeClass("icon-circle-arrow-down").addClass("icon-circle-arrow-right");
		} else
		{
			$(this).closest(".facet").children(".facet-options").slideDown().find(".facet-search").focus();
			$(this).find("i").addClass("icon-circle-arrow-down").removeClass("icon-circle-arrow-right");
			
		}
	});
	
	// Enables searching facets
	$("body").on("keyup", ".facet-search", function(event)
	{
		if(event.keyCode == 27)
		{
			$(this).val("");
		}
		var val = $(this).val().toLowerCase();
		if(val == "")
		{
			$(this).closest(".facet-options").find("ul li").show();
		} else
		{
			console.log(val)
			$(this).closest(".facet-options").find("ul li").each(function()
			{
				if($(this).text().toLowerCase().indexOf(val) >= 0)
				{	
					$(this).show();
				} else
				{
					
					$(this).hide();
				}
			})
		}
		
	});

	
	// Hide unnecessary facets!
	$('.facet').each(function()
	{
		if($(this).find(".facet-options li").length == 0)
		{
			$(this).hide();
		}
		
		if($('.facet').is(":visible").length == 0)
		{
			$("<p>No facets available.</p>").insertAfter($('.browse-facets header'));
		}
	});
}



// Enables popup images in the CMS
function initPopupIMG()
{
	$('a[rel="popupImg"]').on('click', function(event)
	{
		event.preventDefault();
		event.stopPropagation();

		// Load the image!
		$('.image-popup .title').text($(this).text());
		$('.image-popup img').attr('src', $(this).attr('href')).load(function()
			{
				$('.image-popup').fadeIn();
			});

		$('.image-popup .controls a[data-action="close"]').on('click', function(event)
		{
			event.preventDefault();
			event.stopPropagation();
			$('.image-popup').fadeOut();
		});
	});
}


// Enables the fancy site navigation
function initSiteNav()
{
	if($('.site-nav').length)
	{
		// Buttons!
		$(".site-details section").each(function()
		{
			if($(this).attr("id"))
			{
				$('.site-nav').append("<a href='#" + $(this).attr("id") + "' class='" + $(this).attr('id') + "'><i class='icon icon-circle-blank'></i><span class='text'>" + $(this).find("h2").text() + "</span></a>");
			}
		});
		
		$($(".site-nav").find("a")[0]).addClass("active");
		
		// scrolling movement
		
	    $(document).scroll(function() {
			
			var scr = $(this).scrollTop();
			var top = $(".site-nav").parent().offset().top;
			if(scr > top)
			{
				if((scr + $(window).height() + 100) < $(document).height())
				{
					$(".site-nav").css({"margin-top" : scr-top + "px"});
				}
			} else
			{
				$(".site-nav").css({"margin-top":"0px"});
			}
			
			var found = false;
			$($(".site-details section").get().reverse()).each(function()
			{
				if(scr > $(this).offset().top && $(this).attr("id"))
				{
					found = true;
					if(!$('.site-nav').find("a." + $(this).attr("id")).hasClass("active"))
					{
						$('.site-nav a').removeClass("active");
						$('.site-nav').find("a." + $(this).attr("id")).addClass("active")
					}
					
					return false;
				}
				if(!found)
				{
					$($('.site-nav a').removeClass("active")[0]).addClass("active");
				}
			});
	    });
		
	}
}

function initSlideshow()
{
	if($("#slides").length > 0)
	{
		/*
		STEPS:
			1. move img.slideshow > #slides
			2. delete empty <p> tags
			3. setup slideshow
		*/
		$("img.slideshow").appendTo("#slides");
		
		//2
		$('p').filter(function () { return $.trim(this.innerHTML) == "" || $.trim(this.innerHTML) == "&nbsp;" }).remove();
		
		// 3
		$('#slides').slidesjs({
		        height: 300,
		        play: {
		          active: true,
		          auto: true,
		          interval: 4000,
		          swap: true,
		          pauseOnHover: true,
		          restartDelay: 2500
		        }
		      });
	}	
}

function initTooltips()
{
	$("*").tooltip();
}
function initViewOptions()
{
	$("body").on("click", ".view-options .grid", function(event)
	{
		event.preventDefault();
		browseSwitchToGrid();
		$(".view-options .current").removeClass("current");
		
		$(this).addClass("current");
		cookie_set("view_options", "grid", 365);
	});
	
	
	$("body").on("click", ".view-options .list", function(event)
	{
		event.preventDefault();
		browseSwitchToList();
		$(".view-options .current").removeClass("current");
		
		$(this).addClass("current");
		cookie_set("view_options", "list", 365);
	});
	
	$("body").on("click", ".view-options .map_display", function(event)
	{
		event.preventDefault();
		if($(this).hasClass("on"))
		{
			$("#map").slideUp();
			$(this).removeClass("on").find("span").text("Show Map");
		} else
		{
			$("#map").slideDown("fast", function()
			{
				map.invalidateSize(false);
			});
			
			$(this).addClass("on").find("span").text("Hide Map");
		}
	});
	
	// Switch to icons if needed!
	if(cookie_get("view_options") == "grid" || !$(".view-options").length)
	{
		browseSwitchToGrid();
	}
}

function rotateHomepage()
		{
			if(image == 3) 
			{
				image = 1;
			} else
			{
				image++;
			}
			
			$(".site-header.home").css({"background-image" : "url('static/frontend-assets/img/header/carousel/sample" + image + ".jpg')" });
			$(".site-header .switcher i.icon-sign-blank").removeClass("icon-sign-blank").addClass("icon-check-empty");
			$($(".site-header .switcher i")[image-1]).addClass("icon-sign-blank").removeClass("icon-check-empty");
			
		}
// Here's where the magic happens!
$(document).ready(function()
{
	initBrowseMap();
	initDynamicSearch();
	initImageBrowser();
	initFaceting();
	initSlideshow();
	initHomeHeader();
	initPopupIMG();
	initSiteNav();
	initTooltips();
	initViewOptions();
});