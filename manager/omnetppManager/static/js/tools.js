/* general tools for handling forms */

/**
 * Add listeners to form
 */
function initEventListeners(){
    var addFormRows = document.querySelectorAll(".add-form-row");
    for (i=0; i<addFormRows.length; i++){
        addFormRows[i].addEventListener("click", addRowListener);
    }

    var rmFormRows = document.querySelectorAll(".remove-form-row");
    for (i=0; i<rmFormRows.length; i++){
        rmFormRows[i].addEventListener("click", rmRowListener);
    }
}

/*
 * Add the listener for adding an additional row
 */
function addRowListener(e){
    e.preventDefault();
    addElement('form', e.target);
    return false;
}

/*
 * Add the listener for removing a row
 */
function rmRowListener(e){
    e.preventDefault();
    rmElement('form', e.target);
    return false;
}


/*
 * Add an element for a given row
 */
function addElement(prefix, actor){
    var form = closest(actor, "form");
    actor.removeEventListener("click", addRowListener);

    var row = closest(actor, "tr");
    var newRow = row.cloneNode(true);


    // Remove errors when row is cloned
    var errorElements = newRow.querySelectorAll("span.error");
    if (errorElements != null){
        errorElements.forEach(function (element) {
            element.remove();
        });
    }

    actor.addEventListener("click", rmRowListener);
    actor.classList.remove('btn-success');
    actor.classList.add('btn-danger');
    actor.classList.remove('add-form-row');
    actor.classList.add('remove-form-row');
    actor.innerHTML = "-";


    var newRowButton = newRow.querySelector("button");
    newRowButton.addEventListener("click", addRowListener);

    row.parentNode.appendChild(newRow);
    updateIndices(form);
    return false;
}

/*
 * Remove an element
 */
function rmElement(prefix, actor){
    var form = closest(actor, "form");
    closest(actor, "tr").remove();
    updateIndices(form);
    return false;
}

/*
 * Update the form elements (id, name etc.)
 */
function updateIndices(form){
    var totalRowsInput = form.querySelector('[id$="-TOTAL_FORMS"]');
    var prefix = totalRowsInput.id.replace("-TOTAL_FORMS", "");
    prefix = prefix.replace("id_", "");

    var tbody = form.querySelector("tbody"); // ignore row for heading
    var formRows = tbody.querySelectorAll("tr");

    var totalRows = 0;

    for (i=0; i<formRows.length; i++){
        totalRows = i + 1
        var elements = formRows[i].querySelectorAll("select, input");
        if (elements != null){
            elements.forEach( function(element) {
                // ignore some buttons
                if (["submit", "reset"].indexOf(element.type) == -1){
                    var oldName = element.name;
                    var oldNumber = parseInt(oldName.replace(prefix+"-", "").split("-")[0], 0);
                    var remainder = oldName.replace(prefix+"-"+oldNumber+"-", "");
                    var newName = prefix + "-" + i + "-" + remainder;
                    element.id = element.id.replace("id_"+oldName, "id_"+newName);
                    element.name = element.name.replace(oldName, newName);
                }
            });
        }

        var forElements = formRows[i].querySelector("label");
        if (forElements != null){
            forElements.forEach(function(element){
                var oldName = element.for;
                var oldNumber = parseInt(oldName.replace(prefix+"-", "").split("-")[0], 0);
                var remainder = oldName.replace(prefix+"-"+oldNumber+"-", "");
                var newName = prefix + "-" + i + "-" + remainder;
                element.for = element.for.replace(oldName, newName);
            });
        }
    }

    totalRowsInput.value = totalRows;

    return;
}


/**
 * Find closest element travelling the DOM upwards
 */
function closest(el, selector) {
    var matchesFn;
    ['matches','webkitMatchesSelector','mozMatchesSelector','msMatchesSelector','oMatchesSelector'].some(function(fn) {
        if (typeof document.body[fn] == 'function') {
            matchesFn = fn;
            return true;
        }
        return false;
    })

    var parent;

    while (el) {
        parent = el.parentElement;
        if (parent && parent[matchesFn](selector)) {
            return parent;
        }
        el = parent;
    }

    return null;
}
