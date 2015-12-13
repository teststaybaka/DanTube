$(document).ready(function() {
  $('tr.title').click(function() {
    $(this).next().toggle(200);
  });
});