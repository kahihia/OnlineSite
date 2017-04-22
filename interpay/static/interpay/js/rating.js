

function rating_fun() {

    var email = document.getElementById("email");
    var mobile = document.getElementById("mobile");

    var width_style = document.getElementById("star-ratings-sprite-rating");
    var review_numbers = document.getElementById("count");

    // var currency_select = document.getElementById("currency_code" + index);
    // var converted = document.getElementById("converted" + index);
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