var getElement = function(selector) {
  var elements = [];
  if(selector[0] == '#') {
  elements.push(document.getElementById(selector.substring(1, selector.length)));
  } else if(selector[0] == '.') {
    elements = document.getElementsByClassName(selector.substring(1, selector.length));
  } else {
    elements = document.getElementsByTagName(selector);
  }
  return elements;
}

var hasClass = function(selector, _class) {
        var elements = getElement(selector);
        var contains = false;
        var foundElement
        for (let index = 0; index < elements.length; index++) {
            const curElement = elements[index];
            if(curElement.classList.contains(_class)) {
                contains = true;
                foundElement = curElement;
                break;
            }
        }
        //return contains;
        return foundElement;
    }

function collapsedSidebar() {
  const sideBar = hasClass("button", "w-mr-4");
  try {
  // Your variable is undefined
    sideBar.click();
  } catch(err) {
    console.log(err)
  }
}

document.onreadystatechange = function () {
  if (document.readyState == "complete") {
    collapsedSidebar();
  }
}
