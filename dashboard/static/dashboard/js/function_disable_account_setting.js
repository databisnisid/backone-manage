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
  //if (sideBar) {
  try {
  // Your variable is undefined
    sideBar.click();
  } catch(err) {
    console.log(err)
  }
  //}
}

document.onreadystatechange = function () {
  if (document.readyState == "complete") {
    collapsedSidebar();
    // Find the form and remove it
    var formToDelete = document.querySelector('form[action="/pages/search/"]');
    if (formToDelete) {
      formToDelete.remove();
    }

    formToDelete = document.getElementById('tab-label-notifications');
    if (formToDelete) {
      formToDelete.remove();
    }
    formToDelete = document.getElementById('avatar-section');
    if (formToDelete) {
      formToDelete.remove();
    }
    formToDelete = document.getElementById('locale-section');
    if (formToDelete) {
      formToDelete.remove();
    }

    formToDelete = document.getElementById('theme-section');
    if (formToDelete) {
      formToDelete.remove();
    }

    // Remove Role Tab
    formToDelete = document.getElementById('tab-label-roles');
    if (formToDelete) {
      formToDelete.remove();
    }

    // Remove Assign Role
    formToDelete = document.querySelector('a[href*="/bulk/accounts/user/assign_role/"]');
    if (formToDelete) {
      formToDelete.remove();
    }

    // Remove Assign Role
    formToDelete = document.querySelector('a[href*="/bulk/accounts/user/delete/"]');
    if (formToDelete) {
      formToDelete.remove();
    }
    var elementDisable = document.getElementById('id_username').querySelector('[aria-describedby="description-id"]');
    if (elementDisable) {
      elementDisable.disabled = true;
    }
    /*
    var elementDisable = document.getElementById('id_name_email-first_name');
    if (elementDisable) {
      elementDisable.disabled = true;
    }
    elementDisable = document.getElementById('id_name_email-last_name');
    if (elementDisable) {
      elementDisable.disabled = true;
    }
    elementDisable = document.getElementById('id_name_email-email');
    if (elementDisable) {
      elementDisable.disabled = true;
    }
    */
  }
}


