package com.ythwork.oauth2authorizationcode.web;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class CallbackController {

    @GetMapping("/callback")
    public String callback(@RequestParam(required = false) String code,
                           @RequestParam(required = false) String error) {
        return "code=" + code + ", error=" + error;
    }
}
