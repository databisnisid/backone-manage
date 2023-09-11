// Initialize and add the map
let map;
var markers = [];
var markersCluster = [];
var data_prev = [];
var data_new = [];
var bounds;

var marker_property = {
    'is_problem': {
        'markerColor': '#ffc300', // Yellow
        'glyphColor': "black",
        'glyphBorder': "black",
        'glyphScale': 1.1,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': [],
    },
    'is_online': {
        'markerColor': '#00aa00', // Yellow
        'glyphColor': "white",
        'glyphBorder': "white",
        'glyphScale': 0.9,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': [],
    },
    'is_offline': {
        'markerColor': '#ff0000', // Yellow
        'glyphColor': "white",
        'glyphBorder': "white",
        'glyphScale': 0.8,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': [],
    },
    'is_new': {
        'markerColor': '#0000ff', // Yellow
        'glyphColor': "white",
        'glyphBorder': "white",
        'glyphScale': 1.0,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': [],
    }
};

const intersectionObserverDrop = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (entry.isIntersecting) {
      entry.target.classList.add("drop");
      intersectionObserverDrop.unobserve(entry.target);
    }
  }
});


const intersectionObserverBounce = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (entry.isIntersecting) {
      entry.target.classList.add("bounce");
      intersectionObserverBounce.unobserve(entry.target);
    }
  }
});

// Sets the map on all markers in the array.
function setMapOnAll(map) {
  for (let i = 0; i < markers.length; i++) {
    markers[i].setMap(map);
  }
  for (let i = 0; i < markersCluster.length; i++) {
    markersCluster[i].setMap(map);
  }
  for (let key in marker_property) {
    for (let i = 0; i < marker_property[key].markers.length; i++) {
        marker_property[key].markers.setMap(map);
    }
    for (let i = 0; i < marker_property[key].markersCluster.length; i++) {
        marker_property[key].markersCluster.setMap(map);
        markersCluster[i].setMap(map);
    }
    marker_property[key].markers = [];
    marker_property[key].markersCluster = [];
  }
}

// Removes the markers from the map, but keeps them in the array.
function hideMarkers() {
  setMapOnAll(null);
}

// Shows any markers currently in the array.
function showMarkers() {
  setMapOnAll(map);
}

// Deletes all markers in the array by removing references to them.
function deleteMarkers() {
  hideMarkers();
  markers = [];
  markersCluster = [];
  for (let key in marker_property) {
      marker_property[key].markers = [];
      marker_property[key].markersCluster = [];
  }
}

var markerOpacity = markerOpacityIncrement = 0.05;

var fadeInMarkers = function(markers) {
    var markerConntet;

    if (markerOpacity <= 1) {

        for (var i = 0, len = markers.length; i < len; ++i) {
            markers[i].content.style.opacity = markerOpacity;
        }

        // increment opacity
        markerOpacity += markerOpacityIncrement;

        // call this method again
        setTimeout(function() {
          fadeInMarkers(markers);
        }, 50);

    } else {
          markerOpacity = markerOpacityIncrement; // reset for next use
    }
}

//function drawMarker(data_marker) {
function drawMarker(key) {

    var infowindow = new google.maps.InfoWindow();
    var marker, i;
    var markerColor, pinGlyph;
    var is_online = false;
    var is_problem = false;
    var glyphColor = "black";
    var glyphBorder = "black";
    var glyphScale = 0.8;
    var data_marker = [];

    // Reset Markers
    markers = [];
    marker_property[key].markers = [];
    marker_property[key].markersCluster = [];

    if (key == 'is_online' || key == 'is_offline')
        marker_property[key].map = map;

    //for (i = 0; i < data_marker.length; i++) {  
    for (i = 0; i < marker_property[key].data.length; i++) {  

      data_marker = marker_property[key].data[i];
      //data_marker[i]['is_online'] = 1;
      //data_marker[i]['is_problem'] = 1;

      //if (data_marker[i]['is_online']) {
      //if (data_marker['is_online']) {
      if (key == 'is_online') {
        is_online = true;
        //if (data_marker[i]['is_problem'])
        //if (data_marker['is_problem'])
        if (key == 'is_problem')
            is_problem = true;
      }
      /*

      if (data_marker[i]['is_online'])
        if (data_marker[i]['is_problem']) {
            markerColor = '#ffc300'; // Yellow
            glyphColor = "black";
            glyphBorder = "black";
            glyphScale = 1.1;
        }
        else {
            //markerColor = '#3fff33';  // Green
            markerColor = '#009900';  // Green
            glyphColor = "white";
            glyphBorder = "white";
            glyphScale = 0.9;
        }
      else {
          //markerColor = '#ff5733'; // Red
          markerColor = '#ff0000'; // Red
          glyphColor = "white";
          glyphBorder = "white";
          glyphScale = 0.8;
      }

      if (data_marker[i]['is_new']) {
          markerColor = '#0000ff'; // Red
          glyphColor = "white";
          glyphBorder = "white";
          glyphScale = 1;
      }
      */

      //if (! data_marker[i]['is_problem'])

      //if (data_marker[i]['is_problem']==1 || data_marker[i]['is_new']==1) {
      pinGlyph = new google.maps.marker.PinElement({
          background: marker_property[key].markerColor,
          borderColor: marker_property[key].glyphBorder,
          glyphColor: marker_property[key].glyphColor,
          scale: marker_property[key].glyphScale
      });
          /*
      }
      else {
        pinGlyph = new google.maps.marker.PinElement({
            background: markerColor,
            borderColor: "black",
            glyphColor: glyphColor,
            scale: 0.8
        });
      }
        */

      //if (! data_marker[i]['is_problem'])
      //if (data_marker[i]['is_problem'] || data_marker[i]['is_new']) {
      marker = new google.maps.marker.AdvancedMarkerElement({
          //position: new google.maps.LatLng(data_marker[i]['lat'], data_marker[i]['lng']),
          position: new google.maps.LatLng(data_marker['lat'], data_marker['lng']),
          content: pinGlyph.element,
          map: marker_property[key].map,
          //title: data_marker[i]['name']
          title: data_marker['name']
      });
      //}
          /*
      else {
        marker = new google.maps.marker.AdvancedMarkerElement({
            position: new google.maps.LatLng(data_marker[i]['lat'], data_marker[i]['lng']),
            content: pinGlyph.element,
            title: data_marker[i]['name']
        });
      }
          */

      const content = marker.content;
        // Start - Animation Drop
      content.style.opacity = "0";
      content.addEventListener("animationend", (event) => {
          content.classList.remove("drop");
          content.style.opacity = "1";
          if (is_problem) {
              const time = 5 + Math.random(); // 2s delay for easy to see the animation
              content.style.setProperty("--bounce-delay-time", time + "s");
              intersectionObserverBounce.observe(content);
          }
      });

      const time = 1 + Math.random(); // 2s delay for easy to see the animation

      content.style.setProperty("--delay-time", time + "s");
      intersectionObserverDrop.observe(content);
      // End - Animation Drop

      // Start - Content InfoWindow
      let contentString =
            '<div id="content">' +
            '<div id="siteNotice"></div>' +
            '<h2 id="firstHeading" class="firstHeading">' + data_marker['name'] + '</h2>' +
            '<div id="bodyContent">' +
            '<p>' + data_marker['problem_string'] + '</p>' +
            '<a href="/members/members/?q=' + data_marker['member_id'] + '">CHECK</a>' +
            '</div>' +
            '</div>';

      google.maps.event.addListener(marker, 'click', (function(marker, i) {
        return function() {
          infowindow.setContent(contentString);
          infowindow.open(map, marker);
        }
      })(marker, i));
      // End - Content InfoWindow

      //if (! data_marker[i]['is_problem']==1 || ! data_marker[i]['is_new']==1) {
      if (key == 'is_online' || key == 'is_offline') {
        markers.push(marker);
        marker_property[key].markers.push(marker);
      }
    }

    /*
    if (is_online)
        markerColor = "#009009";
    else
        markerColor = "#ff0000";
          */

    // Start - Renderer
    let customRenderer = new markerClusterer.DefaultRenderer();
    customRenderer.render = function({ count, position }, stats, map) {
        //const color = markerColor;
        const color = marker_property[key].markerColor;
        // create svg literal with fill color
        const svg = `<svg fill="${color}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="50" height="50">
<circle cx="120" cy="120" opacity=".6" r="70" />
<circle cx="120" cy="120" opacity=".3" r="90" />
<circle cx="120" cy="120" opacity=".2" r="110" />
<text x="50%" y="50%" style="fill:#fff" text-anchor="middle" font-size="50" dominant-baseline="middle" font-family="roboto,arial,sans-serif">${count}</text>
</svg>`;

        const title = `Cluster of ${count} markers`;
        // adjust zIndex to be above other markers
        zIndex = Number(google.maps.Marker.MAX_ZINDEX) + count;

        if (map.getMapCapabilities().isAdvancedMarkersAvailable) {
            // create cluster SVG element
            const div = document.createElement("div");
            div.innerHTML = svg;
            const svgEl = div.firstElementChild;
            svgEl.setAttribute("transform", "translate(0 25)");
            const clusterOptions = {
                map,
                position,
                zIndex,
                title,
                content: svgEl,
            };
            markersCluster.push(clusterOptions);
            marker_property[key].markersCluster.push(clusterOptions);
            return new google.maps.marker.AdvancedMarkerElement(clusterOptions);
        }
        const clusterOptions = {
            position,
            zIndex,
            title,
            icon: {
                url: `data:image/svg+xml;base64,${btoa(svg)}`,
                anchor: new google.maps.Point(25, 25),
            },
        };
        markersCluster.push(clusterOptions);
        marker_property[key].markersCluster.push(clusterOptions);
        return new google.maps.Marker(clusterOptions);
    }

    // Add a marker clusterer to manage the markers.
    new markerClusterer.MarkerClusterer({ 
        map: marker_property[key].map,
        markers: marker_property[key].markers,
        renderer: customRenderer
    });
    /*
    new markerClusterer.MarkerClusterer({ 
        map: map,
        markers: markers,
        renderer: customRenderer
    });
    */
}

//async function get_api(api_url) {
async function get_api(base_api, is_all, is_no_org, query_id) {

    var api_url;

    if (is_all)
        api_url = base_api + '/api/members/get_all';
    else
        if (is_no_org)
            api_url = base_api + '/api/members/get_by_user/' + query_id;
        else
            api_url = base_api + '/api/members/get_by_org/' + query_id;

    // Storing response
    const response = await fetch(api_url);
   
    // Storing data in form of JSON
    var data = await response.json();

    console.log(data);
    return data;
}

function arraysEqual(a, b) {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (a.length !== b.length) return false;

  // If you don't care about the order of the elements inside
  // the array, you should sort both arrays here.
  // Please note that calling sort on an array will modify that array.
  // you might want to clone your array first.

  for (var i = 0; i < a.length; ++i) {
    if (JSON.stringify(a[i]) != JSON.stringify(b[i])) {
        return false;
    }
  }
  return true;
}

function setCenterZoom() {

    map.setCenter(bounds.getCenter()); //or use custom center
    map.fitBounds(bounds);

    //remove one zoom level to ensure no marker is on the edge.
    //map.setZoom(map.getZoom() - 1);

    if(map.getZoom() > 15){
        map.setZoom(15);
    }
}

async function redrawMarkers(base_api, is_all, is_no_org, query_id) {
    const { Map, InfoWindow } = await google.maps.importLibrary("maps");
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    var data;

    data_new = await get_api(base_api, is_all, is_no_org, query_id);

    let is_equal = arraysEqual(data_prev, data_new);

    if (! is_equal) {
        data_prev = data_new;
        data = data_new;

        var latlngList = [];
        for (i = 0; i < data.length; i++) {  
            latlngList.push(new google.maps.LatLng(data[i]['lat'], data[i]['lng']));

            bounds = new google.maps.LatLngBounds();
            latlngList.forEach(function(n) {
                bounds.extend(n);
            });
        }

        setCenterZoom();
        /*
        map.setCenter(bounds.getCenter()); //or use custom center
        map.fitBounds(bounds);

        //remove one zoom level to ensure no marker is on the edge.
        //map.setZoom(map.getZoom() - 1);

        if(map.getZoom() > 15){
            map.setZoom(15);
        }
        */

        marker_property.is_new.data = [];
        marker_property.is_online.data = [];
        marker_property.is_offline.data = [];
        marker_property.is_problem.data = [];

        for (i = 0; i < data.length; i++) {  
            if (data[i]['is_new'])
                marker_property.is_new.data.push(data[i]);
            else
                if (data[i]['is_online'])
                    if (data[i]['is_problem'])
                        marker_property.is_problem.data.push(data[i]);
                        //data_problem.push(data[i]);
                    else
                        marker_property.is_online.data.push(data[i]);
                        //data_online.push(data[i])
                else
                    marker_property.is_offline.data.push(data[i]);
                    //data_offline.push(data[i]);
        }
        deleteMarkers();
        for (let key in marker_property)
            drawMarker(key);
            //drawMarker(marker_property[key].data);
        //drawMarker(marker_property.is_online.data);
        //drawMarker(marker_property.is_offline.data);
        //drawMarker(marker_property.is_problem.data);
        //drawMarker(data_online);
        //drawMarker(data_offline);
        //drawMarker(data_problem);
    }
}

//async function initMap(base_api, is_all, is_no_org, query_id) {
async function initMap() {
    // Request needed libraries.
    const { Map, InfoWindow } = await google.maps.importLibrary("maps");
    //const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    map = new Map(document.getElementById("map"), {
      mapId: "MAP_VIEW",
      center: {lat: -1.233982000061532, lng: 116.83728437200422},
      zoom: 5,
    });

}