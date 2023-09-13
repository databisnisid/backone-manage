/*
function waitForElementToExist(selector) {
  return new Promise(resolve => {
    if (document.querySelector(selector)) {
      return resolve(document.querySelector(selector));
    }

    const observer = new MutationObserver(() => {
      if (document.querySelector(selector)) {
        resolve(document.querySelector(selector));
        observer.disconnect();
      }
    });

    observer.observe(document.body, {
      subtree: true,
      childList: true,
    });
  });
}
*/


waitForElementToExist('#id_member_problems-ADD').then(element => {
    console.log('The element exists', element);
    const elements = document.querySelectorAll('[id$="-DELETE-button"]');
    elements.forEach(e => {
        e.style.display = "none";
        console.log(e);
    });
});


/*
setTimeout(() => {

    const elements = document.querySelectorAll('[id$="-DELETE-button"]');
    //let elements = document.querySelectorAll('[title="Delete"]');
    elements.forEach(e => {
        e.style.display = "none";
        console.log(e);
    });

}, 1000);
*/
