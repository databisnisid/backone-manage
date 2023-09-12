// Initialize and add the map
let map;
//var markers = [];
var data_prev = [];
var data_new = [];
var bounds;
var legend;

var marker_property = {
    'is_new': {
        'title': 'NEW',
        'markerColor': '#0000ff', // Yellow
        'glyph': "/static/dashboard/images/backone-white-trans.svg",
        //'glyphColor': "white",
        'glyphColor': "#0000ff",
        'glyphBorder': "white",
        'glyphScale': 1.0,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': null,
        'show': true,
        'is_cluster': false,
        'count': 0,
    },
    'is_online': {
        'title': 'ONLINE',
        'markerColor': '#009900', // Yellow
        'glyph': "/static/dashboard/images/backone-white-trans.svg",
        //'glyphColor': "white",
        'glyphColor': "#009900",
        'glyphBorder': "white",
        'glyphScale': 0.8,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': null,
        'show': true,
        'is_cluster': true,
        'count': 0,
    },
    'is_offline': {
        'title': 'OFFLINE',
        'markerColor': '#ff0000', // Yellow
        'glyph': "/static/dashboard/images/backone-white-trans.svg",
        //'glyphColor': "black",
        'glyphColor': "#ff0000",
        'glyphBorder': "white",
        'glyphScale': 0.9,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': null,
        'show': true,
        'is_cluster': true,
        'count': 0,
    },
    'is_problem': {
        'title': 'PROBLEM',
        'markerColor': '#ffc300', // Yellow
        'glyph': "/static/dashboard/images/backone-black-trans.svg",
        //'glyph': backoneTrans,
        //'glyphColor': "black",
        'glyphColor': "#ffc300",
        'glyphBorder': "black",
        'glyphScale': 1.1,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': null,
        'show': true,
        'is_cluster': false,
        'count': 0,
    },
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
    /*
  for (let i = 0; i < markers.length; i++) {
    markers[i].setMap(map);
  }
  for (let i = 0; i < markersCluster.length; i++) {
    markersCluster[i].setMap(map);
  }
    */
  for (let key in marker_property) {
    for (let i = 0; i < marker_property[key].markers.length; i++) {
        marker_property[key].markers[i].setMap(map);
    }
    //for (let i = 0; i < marker_property[key].markersCluster.length; i++) {
        //marker_property[key].markersCluster[i].setMap(map);
    if (marker_property[key].markersCluster != null)
        marker_property[key].markersCluster.clearMarkers();
        //markersCluster[i].setMap(map);
    //}
    //marker_property[key].markers = [];
    //marker_property[key].markersCluster = [];
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
  for (let key in marker_property) {
      marker_property[key].markers = [];
      marker_property[key].markersCluster = null;
  }
}


function drawMarker(key) {

    var infowindow = new google.maps.InfoWindow();
    var marker, i;
    var pinGlyph;
    var data_marker = [];
    var return_renderer;

    // Reset Markers
    marker_property[key].markers = [];
    marker_property[key].markersCluster = [];

    //if (key == 'is_new' || key == 'is_problem')
    if (! marker_property[key].is_cluster)
        marker_property[key].map = map;

    for (i = 0; i < marker_property[key].data.length; i++) {  

      data_marker = marker_property[key].data[i];
      //data_marker['is_online'] = true;
      //data_marker['is_problem'] = true;
      const glyphImg = document.createElement("img");
      //backoneTrans.src = "/static/dashboard/images/backone.svg";
      glyphImg.src = marker_property[key].glyph;

      pinGlyph = new google.maps.marker.PinElement({
          background: marker_property[key].markerColor,
          borderColor: marker_property[key].glyphBorder,
          glyphColor: marker_property[key].glyphColor,
          //glyph: marker_property[key].glyph,
          glyph: glyphImg,
          scale: marker_property[key].glyphScale
      });

      marker = new google.maps.marker.AdvancedMarkerElement({
          position: new google.maps.LatLng(data_marker['lat'], data_marker['lng']),
          content: pinGlyph.element,
          map: marker_property[key].map,
          title: data_marker['name']
      });

      const content = marker.content;
      // Start - Animation Drop
      content.style.opacity = "0";
      content.addEventListener("animationend", (event) => {
          content.classList.remove("drop");
          content.style.opacity = "1";
          if (key == 'is_problem') {
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

      //if (key == 'is_online' || key == 'is_offline') {
        marker_property[key].markers.push(marker);
      //}
    }

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

        return new google.maps.Marker(clusterOptions);
    }

    // Add a marker clusterer to manage the markers.
    if (marker_property[key].is_cluster) {
        let markersCluster = new markerClusterer.MarkerClusterer({ 
            map: map,
            markers: marker_property[key].markers,
            renderer: customRenderer
        });
        marker_property[key].markersCluster = markersCluster;
        //console.log(marker_property[key].markersCluster);
    }
    else {
        marker_property[key].markersCluster = null;
    }
    //console.log(marker_property[key].markers);
}


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

    //console.log(data);
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

//async function redrawMarkers(base_api, is_all, is_no_org, query_id) {
async function redrawMarkers() {
    const { Map, InfoWindow } = await google.maps.importLibrary("maps");
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    var data;
    var is_equal = false;

    if (api_params.new_query) {
        data_new = await get_api(
            api_params.api_url, api_params.is_all, 
            api_params.is_no_org, api_params.query_id);

        is_equal = arraysEqual(data_prev, data_new);
    }

    //let is_equal = arraysEqual(data_prev, data_new);

    //if (! is_equal || api_params.new_query == false) {
    //console.log(data_new);
    if (! is_equal) {
        //console.log(data_prev);
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
                    else
                        marker_property.is_online.data.push(data[i]);
                else
                    marker_property.is_offline.data.push(data[i]);
        }
        deleteMarkers();
        for (let key in marker_property) {
            marker_property[key].count = marker_property[key].data.length;
            if (marker_property[key].show && marker_property[key].data.length > 0)
                drawMarker(key);

            // Remove Element
            var divRemove = document.getElementById(key);
            if (divRemove)
                divRemove.remove()

            // Create Legend
            var div = document.createElement('div');
            div.id = key;
            div.innerHTML =  '<span style="color: black;">' +
                marker_property[key].title + 
                ': ' + marker_property[key].count + '</span>';
            legend.appendChild(div);
        }
    }
}

/**
 * Creates a control that recenters the map on Chicago.
 */
function createCenterControl(map) {
  const controlButton = document.createElement("button");

  // Set CSS for the control.
  controlButton.style.backgroundColor = "#fff";
  controlButton.style.border = "2px solid #fff";
  controlButton.style.borderRadius = "3px";
  controlButton.style.boxShadow = "0 2px 6px rgba(0,0,0,.3)";
  controlButton.style.color = "rgb(25,25,25)";
  controlButton.style.cursor = "pointer";
  controlButton.style.fontFamily = "Roboto,Arial,sans-serif";
  controlButton.style.fontSize = "16px";
  controlButton.style.lineHeight = "38px";
  controlButton.style.margin = "8px 0 22px";
  controlButton.style.padding = "0 5px";
  controlButton.style.textAlign = "center";
  controlButton.textContent = "Show All Sites";
  controlButton.title = "Click to recenter the map and show all sites";
  controlButton.type = "button";
  // Setup the click event listeners: simply set the map to Chicago.
  controlButton.addEventListener("click", () => {
    setCenterZoom();
  });
  return controlButton;
}

function createHideOnlineControl(map) {
  const controlButton = document.createElement("button");

  // Set CSS for the control.
  controlButton.style.backgroundColor = "#fff";
  controlButton.style.border = "2px solid #fff";
  controlButton.style.borderRadius = "3px";
  controlButton.style.boxShadow = "0 2px 6px rgba(0,0,0,.3)";
  controlButton.style.color = "rgb(25,25,25)";
  controlButton.style.cursor = "pointer";
  controlButton.style.fontFamily = "Roboto,Arial,sans-serif";
  controlButton.style.fontSize = "16px";
  controlButton.style.lineHeight = "38px";
  controlButton.style.margin = "8px 3px 22px";
  controlButton.style.padding = "0 5px";
  controlButton.style.textAlign = "center";
  controlButton.textContent = "Toggle Cluster";
  controlButton.title = "Click to toggle clustering";
  controlButton.type = "button";
  // Setup the click event listeners: simply set the map to Chicago.
  controlButton.addEventListener("click", () => {
    for (let key in marker_property) {
        if (marker_property[key].is_cluster) {
            marker_property[key].is_cluster = false;
        }
        else {
            if (key == 'is_online')
                marker_property[key].is_cluster = true;

            if (key == 'is_offline')
                marker_property[key].is_cluster = true;
        }
    }
    api_params.new_query = false;
    redrawMarkers();
    //console.log(api_params);
  });
  return controlButton;
}

async function initMap() {
    // Request needed libraries.
    const { Map, InfoWindow } = await google.maps.importLibrary("maps");
    //const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    map = new Map(document.getElementById("map"), {
      mapId: "MAP_VIEW",
      center: {lat: -1.233982000061532, lng: 116.83728437200422},
      zoom: 5,
      mapTypeControl: true,
      mapTypeControlOptions: {
        style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
        mapTypeIds: ["roadmap", "terrain"],
    },
    });

    // Create the DIV to hold the control.
    const centerControlDiv = document.createElement("div");
    // Create the control.
    const centerControl = createCenterControl(map);

    const hideOnlineDiv = document.createElement("div");
    const hideOnline = createHideOnlineControl(map);

    // Append the control to the DIV.
    centerControlDiv.appendChild(centerControl);
    map.controls[google.maps.ControlPosition.TOP_CENTER].push(centerControlDiv);

    hideOnlineDiv.appendChild(hideOnline);
    map.controls[google.maps.ControlPosition.TOP_CENTER].push(hideOnlineDiv);

    legend = document.getElementById("legend");
    map.controls[google.maps.ControlPosition.RIGHT_TOP].push(legend);

}
