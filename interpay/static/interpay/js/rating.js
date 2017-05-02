

function rating_fun() {

    var email = document.getElementById("email");
    var mobile = document.getElementById("mobile");

    var width_style = document.getElementById("star-ratings-sprite-rating");
    var review_numbers = document.getElementById("count");

    $.ajax({
        url: "/rating_by_email/", // the endpoint
        type: "GET", // http method
        data: {email:email.value , mobile:mobile.value}, // data sent with the post request

        // handle a successful response
        success: function (json) {
             width_style.style.width=json['result']* 22;
            review_numbers.innerHTML = json['result2'];
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: " + errmsg +
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
    // var form =document.getElementById("convertButton"+ index);
    // form.style.display = "block";


}


function find_reviewing_user(LANGUAGE_CODE){

        var email = document.getElementById("email");
        var mobile = document.getElementById("mobile");
        // var reviewing_id = document.getElementById("reviewing_id");

        $.ajax({
        url: "/reviewing_id/", // the endpoint
        type: "GET", // http method
        data: {email:email.value , mobile:mobile.value}, // data sent with the post request

        // handle a successful response
        success: function (json) {
             var reviewing_id = json['result'];
             // win.document.write("Hello world!");
             // console.log(reviewing_id)
            // alert(LANGUAGE_CODE);
            if (LANGUAGE_CODE =='en-gb')
                window.location.href = '/review_comments/' + reviewing_id;
            else
                window.location.href = '/fa-ir/review_comments/' + reviewing_id;
            end
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: " + errmsg +
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}